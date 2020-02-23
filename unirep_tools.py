import tensorflow as tf
import numpy as np
import os
from data_IO import download_folder_from_s3

BUCKET = 'metaflow-metaflows3bucket-g7dlyokq680q'
LOCAL_WEIGHT_PATH = 'weights/'

def save_weights(sess, save_path="output/"):
        """
        Saves the weights of the model in dir_name in the format required 
        for loading in this module. Must be called within a tf.Session
        For which the weights are already initialized.
        """
        vs = tf.trainable_variables()
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        for v in vs:
            name = v.name
            value = sess.run(v)
            # print(name)
            # print(value)
            np.save(os.path.join(save_path,name.replace('/', '_') + ".npy"), np.array(value))
        return(save_path)
            
def fit(seqs, vals, 
        save_path="output/",
        weights_path=None,
        batch_size=256, 
        model_size=64, 
        end_to_end=False, 
        learning_rate=.001):
    
    # Set seeds
    tf.set_random_seed(42)
    np.random.seed(42)

    # Download starting weights
    if weights_path is None:
        if model_size==1900: weights_path = "models/UniRep/base1900/"
        elif model_size==64: weights_path = "models/UniRep/base64/"
    local_weight_path = download_folder_from_s3(s3_path=weights_path, directory=LOCAL_WEIGHT_PATH, bucket=BUCKET)

    # Import babbler
    if model_size==1900: from unirep import babbler1900 as babbler # Import the mLSTM babbler model
    elif model_size==64: from unirep import babbler64   as babbler # Import the mLSTM babbler model

    # Initialize UniRep
    b = babbler(batch_size=batch_size, model_path=local_weight_path)
    
    # Format input
    with open("formatted.txt", "w") as destination:
        for i,(seq,val) in enumerate(zip(seqs,vals)):
            seq = seq.strip()
            if b.is_valid_seq(seq) and len(seq) < 275:
                formatted = ",".join(map(str,b.format_seq(seq)))
                formatted = str(int(round(val)))+","+formatted
                if end_to_end: formatted = formatted+","+str(25) # append stop to end of sequence
                destination.write(formatted)
                destination.write('\n')

    # Bucket data
    bucket_op = b.bucket_batch_pad("formatted.txt", interval=1000) # Large interval

    # Obtain all of the ops needed to output a representation
    final_hidden, x_placeholder, batch_size_placeholder, seq_length_placeholder, initial_state_placeholder = (
        b.get_rep_ops())
    # `final_hidden` should be a batch_size x rep_dim matrix.

    # Default model: train a basic feed-forward network as the top model, doing regression with MSE loss, and the Adam optimizer. We can do that by:
    # 1.  Defining a loss function.
    # 2.  Defining an optimizer that's only optimizing variables in the top model.
    # 3.  Minimizing the loss inside of a TensorFlow session
    y_placeholder = tf.placeholder(tf.float32, shape=[None,1], name="y")
    initializer = tf.contrib.layers.xavier_initializer(uniform=False)
    with tf.variable_scope("top"):
        prediction = tf.contrib.layers.fully_connected(
            final_hidden, 1, activation_fn=None,
            weights_initializer=initializer,
            biases_initializer=tf.zeros_initializer()
        )
    loss = tf.losses.mean_squared_error(y_placeholder, prediction)

    # You can specifically train the top model first by isolating variables of the "top" scope, and forcing the optimizer to only optimize these.
    optimizer = tf.train.AdamOptimizer(learning_rate)
    if not end_to_end:
        top_variables = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope="top")
        step_op = optimizer.minimize(loss, var_list=top_variables)
    else:
        step_op = optimizer.minimize(loss)

    # We next need to define a function that allows us to calculate the length each sequence in the batch so that we know what index to use to obtain the right "final" hidden state
    def nonpad_len(batch):
        nonzero = batch > 0
        lengths = np.sum(nonzero, axis=1)
        return lengths

    # Train model
    num_iters = 50
    Loss = []
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        for i in range(num_iters):
            batch = sess.run(bucket_op)
            y = batch[:,0]
            y = list(map(lambda val:[val], y))
            batch = batch[:,1:]
            length = nonpad_len(batch)
            loss_, __, = sess.run([loss, step_op],
                    feed_dict={
                            x_placeholder: batch,
                            y_placeholder: y,
                            batch_size_placeholder: batch_size,
                            seq_length_placeholder:length,
                            initial_state_placeholder:b._zero_state
                    }
            )
            Loss.append(loss_)
            print("Iteration {0}: {1}".format(i, loss_))
        save_weights(sess, save_path)
        
    return(Loss, save_path)