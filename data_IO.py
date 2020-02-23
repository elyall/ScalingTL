import urllib
import gzip
from zipfile import ZipFile
import shutil
import boto3
import os
import pandas as pd
import json

LOCAL_PATH = os.getcwd()
S3_PATH = "data/"
BUCKET = "metaflow-metaflows3bucket-g7dlyokq680q"

def download_url(url, directory=LOCAL_PATH, remove_zip=True):
    ext = url.split(".")[-1]
    name = url.split("/")[-1]
    file_path = os.path.join(directory, name)
    try:
        # Download file
        print("Downloading " + url)
        with urllib.request.urlopen(url) as r:
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(r, f)
                f.seek(0)

        # Unzip & save
        orig_path = file_path
        if ext=="gz":
            print("Unzipping " + file_path)
            with gzip.open(file_path, 'rb') as f_in:
                with open(file_path[:-3], 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            file_path = file_path[:-3]
            if remove_zip: os.remove(orig_path)
        elif ext=="zip":
            print("Unzipping " + file_path)
            with ZipFile(file_path, 'r') as zip_ref:
                extracted = zip_ref.namelist()
                zip_ref.extractall(directory)
            file_path = [os.path.join(directory, f) for f in extracted]
            if remove_zip: os.remove(orig_path)
        
        return(file_path)
    except:
        print("Failed: " + file_path)

def parse_s3_path(s3_path):
    if s3_path.startswith('s3://'): s3_path = s3_path[5:]
    contents = s3_path.split('/')
    bucket = contents[0]
    key = '/'.join(contents[1:])
    filename = contents[-1]
    return(bucket, key, filename)
    
def upload_file_to_s3(file_path, key=None, s3_path=None, bucket=BUCKET, s3_client=None):
    if key is None: key = os.path.basename(file_path) # assume filepath input
    if s3_path: key = os.path.join(s3_path, key)
    if not s3_client: s3_client = boto3.client('s3')
    if isinstance(file_path, str):
        response = s3_client.upload_file(file_path, bucket, key)
    else:
        response = s3_client.upload_fileobj(file_path, bucket, key)
    return(response, key)

def upload_folder_to_s3(directory, s3_path=S3_PATH, bucket=BUCKET):
    responses = []
    s3_client = boto3.client('s3')
    for root,dirs,files in os.walk(directory):
        for file in files:
            file_path = file
            if s3_path: file_path = os.path.join(s3_path,file_path)
            responses.append(s3_client.upload_file(os.path.join(root,file), bucket, file_path))
    return(responses)

def upload_urls_to_s3(urls, s3_path=S3_PATH, bucket=BUCKET):
    urls = [urls] if isinstance(urls, str) else urls
    download_paths = [download_url(url) for url in urls]
    file_paths = []
    for i in download_paths:
        if hasattr(i, '__iter__'):
            for j in i:
                file_paths.append(j)
        else:
            file_paths.append(i)
    responses, keys = [], []
    for f in file_paths:
        r, k = upload_file_to_s3(f, s3_path=s3_path, bucket=bucket)
        responses.append(r)
        keys.append(k)
    return(responses, keys)

def download_obj_from_s3(key, bucket=BUCKET, directory=LOCAL_PATH, filename=None):
    if key.startswith('s3://'): bucket, key, _ = parse_s3_path(key)
    if filename is None: filename = os.path.basename(key)
    file_path = os.path.join(directory, filename) if directory else filename
    s3_client = boto3.client('s3')
    s3_client.download_file(bucket, key, file_path)
    return(file_path)

def download_folder_from_s3(s3_path, directory=os.getcwd(), recursive=False, bucket=BUCKET):
    if s3_path.startswith('s3://'): bucket, s3_path, _ = parse_s3_path(s3_path)
    if not s3_path.endswith('/'): s3_path = s3_path + '/'
    s3 = boto3.resource('s3')
    bucket_obj = s3.Bucket(bucket)
    for object in bucket_obj.objects.filter(Prefix = s3_path):
        key = object.key.split(s3_path)[-1]
        if '/' in key and not recursive:
            continue
        file_path = os.path.join(directory, os.path.dirname(key))
        if not os.path.exists(file_path): os.makedirs(file_path)
        bucket_obj.download_file(object.key, os.path.join(file_path, os.path.basename(object.key)))
    return(directory)

def datasets(name="mhc1", directory=LOCAL_PATH, save_to_csv=False):
    if name=="mhc1":
        filename = "bdata.20130222.mhci.txt"
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path): 
            if not os.path.exists(directory): os.makedirs(directory)
            download_obj_from_s3(S3_PATH + filename, filename=filename, directory=directory, bucket=BUCKET)
        data = pd.read_csv(file_path, delimiter="\t")
        sel = data[(data["species"]=="human") & (data["inequality"]=="=")]
        if save_to_csv: sel[["sequence","meas"]].rename({"meas": "mhci affinity"}).to_csv(filename[:-3]+"csv", index=False)
        seq = sel["sequence"].tolist()
        val = sel["meas"].tolist()
    return(seq, val, data)

def init_base_models():
    meta = {"flow":'UniRep', "id":'base64', "data_file":'uniref50.fasta', "features":'', "size":64, "start":None, "finish":None, "mse":None}
    with open('metadata.json', 'w') as f:
        json.dump(meta, f)
    upload_file_to_s3('metadata.json', s3_path='models/UniRep/base64')
    meta = {"flow":'UniRep', "id":'base1900', "data_file":'uniref50.fasta', "features":'', "size":1900, "start":None, "finish":None, "mse":None}
    with open('metadata.json', 'w') as f:
        json.dump(meta, f)
    upload_file_to_s3('metadata.json', s3_path='models/UniRep/base1900')
    os.remove('metadata.json')