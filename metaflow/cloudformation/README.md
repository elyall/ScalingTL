From https://github.com/Netflix/metaflow-tools/blob/master/aws/cloudformation/README.md

## Using This Template
---
### Overview

This CloudFormation template deploys all the necessary infrastucture in AWS to support Metaflow's integration points and extend its capabilities into the Cloud.  A brief snapshot of its components are as follows:

- **Amazon S3 Bucket** - Metaflow uses Amazon S3 as a centralized data repository for all data that's leveraged by and generated for its flows.  This template creates a dedicated private bucket and all appropriate permissions.

- **AWS Batch Compute Environment** - In order to extend Metaflow's compute capabilities to the cloud, AWS Batch provides a simple API that runs container-based jobs to completion on AWS Elastic Container Service.

- **Amazon Sagemaker Notebook Instance** - Metaflow's API allows for easy access to flow results and information which can be cleanly displayed in a Jupyter notebook.  Amazon Sagemaker Notebook instances provide a fully managed notebook environment with dedicated and customizable compute resources.

- **Metadata Service on AWS Fargate and Amazon Relational Database Service** - To facilitate persistent programmatic access to flow information, Metaflow provides a Metadata service that can be run on cloud resources and enable remote accessibility.  This CloudFormation template leverages AWS Fargate and Amazon Relational Database Service to deploy the Metadata Service Automatically.

- **Amazon API Gateway** - To provide secure, encrypted access to a user's Metadata Service, this CloudFormation template uses Amazon API Gateway as a TLS termination point and an optional point of basic API authentication via key.

- **Amazon VPC Networking** - All underlying network components are deployed to facilitate connectivity for the resources leveraged by Metaflow.  Specifically, a VPC with (2) customizable subnets and Internet connectivity will be leveraged for this template.

- **AWS Identity and Access Management** - Roles specific to Metaflow will be provisioned by this template in order to provide "principle of least privilege" access to resources such as AWS Batch and Amazon Sagemaker Notebook instances.  Additionally, an optional role can be created that provides restricted access to only the resources Metaflow requires.  This allows an easy path of utilization to users who don't need full access to all AWS resources.

### Prerequisites

1. An ECS Instance Role for AWS Batch.  AWS Batch leverages ECS container instances and their respective ECS agents to query various AWS API's.  This template doesn't deploy a role for those instances, as it's a one-time creation that many users will already have, and CloudFormation deployment will fail if the resource already exists.  Instructions for checking for and creating the role can be found [here](https://docs.aws.amazon.com/batch/latest/userguide/instance_IAM_role.html).  Please note that the role **MUST** be named "ecsInstanceRole" and have only the "AmazonEC2ContainerServiceforEC2Role" managed policy attached.
2. Adequate permissions to deploy all CloudFormation resources within an AWS account.

### How To Deploy from the AWS Console

1. Navigate to "Services" and select "CloudFormation" under the "Management and Governance" heading (or search for it in the search bar).
2. Click "Create stack" and select "With new resources (standard)".
3. Ensure "Template is ready" remains selected, choose "Upload a template file", and click "Choose file".
4. Feel free to explore with "View in Designer" if you so choose, otherwise click "Next".
5. Name your stack, select your parameters, and click "Next", noting that if you enable "APIBasicAuth" and/or "CustomRole", further configuration will be required after deployment.  More info below.
6. If desired, feel free to tag your stack in whatever way best fits your organization.  When finished, click "Next".
7. Ensure you select the check box next to "I acknowledge that AWS CloudFormation might create IAM resources." and click "Create stack".
8. Wait roughly 10-15 minutes for deployment to complete.  The Stack status will eventually change to "CREATE_COMPLETE".

Once complete, you'll find an "Outputs" tab that contains values for the components generated by this CloudFormation template.  Those values correlate to respective environment variables (listed next to the outputs) you'll set to enable cloud features within Metaflow.

### Additional Configuration

Did you choose to enable "APIBasicAuth" and/or "CustomRole" and are wondering how they work?  Then you're in the right place!  Below are some details on what happens when those features are enabled and how to make use of them.

- **APIBasicAuth** - In addition to TLS termination, Amazon API Gateway provides the ability to generate an API key that restricts access only to requests that pass that API key in the 'x-api-key' HTTP header.  This is useful in that it restricts access to flow information from the general Internet while still allowing remote connectivity to authenticated clients.  However, enabling this feature means that you'll need to request the API Key from Amazon API Gateway, as exposing a credential as an output from CloudFormation is a potential security problem.  CloudFormation does, however, output the ID of the API Key that correlates to your stack, making is easy to get the key and pass it to Metaflow.  Follow one of the two instructions below to output the key, and then export it to the `METAFLOW_SERVICE_AUTH_KEY` environment variable.

    1. From the AWS CLI, run the following: `aws apigateway get-api-key --api-key <YOUR_KEY_ID_FROM_CFN> --include-value | grep value`
    2. From the AWS Console, navigate to "Services" and select "API Gateway" from "Networking & Content Delivery" (or search for it in the search bar).  Click your API, select "API Keys" from the left side, select the API that corresponds to your Stack name, and click "show" next to "API Key".

- **CustomRole** - This template can create an optional role that can be assumed by users (or applications) that includes limited permissions to only the resources required by Metaflow, including access only to the Amazon S3 bucket, AWS Batch Compute Environment, and Amazon Sagemaker Notebook Instance created by this template.  You will, however, need to modify the trust policy for the role to grant access to the principals (users/roles/accounts) who will assume it, and you'll also need to have your users configure an appropriate role-assumption profile.  The ARN of the Custom Role can be found in the "Output" tab of the CloudFormation stack under `MetaflowUserRoleArn`.  To modify the trust policy to allow new principals, follow the directions [here](https://docs.aws.amazon.com/IAM/latest/UserGuide/roles-managingrole-editing-console.html#roles-managingrole_edit-trust-policy).  Once you've granted access to the principals of your choice, have your users create a new Profile for the AWS CLI that assumes the role ARN by following the directions [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-role.html).