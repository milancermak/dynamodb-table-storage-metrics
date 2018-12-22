# sam-dynamodb-table-storage-metrics
[![Build Status](https://travis-ci.com/milancermak/dynamodb-table-storage-metrics.svg?branch=master)](https://travis-ci.com/milancermak/dynamodb-table-storage-metrics)

A simple [SAM](https://github.com/awslabs/serverless-application-model) app that automatically publishes DynamoDB table storage metrics to Cloudwatch. The application consists of only a single Lambda function that is periodically invoked by a CloudWatch trigger. Once the application is deployed, it is maintenance-free. You can then use the new metrics it creates to monitor your DynamoDB table usage.

The application is [available in the Serverless application repository](https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:790194644437:applications~dynamodb-table-storage-metrics).

## Building and deploying
If you don't want to deploy the app through SAR, you can do the following to have get it running:

```bash
sam build
sam package --s3-bucket ARTIFACTS_BUCKET_NAME --output-template-file packaged.yaml
sam deploy --template-file packaged.yaml --stack-name STACK_NAME --capabilities CAPABILITY_IAM --parameter-overrides MetricNamespace=YourCustomNamespace
```
