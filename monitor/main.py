import datetime
import logging
import os

from botocore.exceptions import ClientError
import boto3


cloudwatch = boto3.client('cloudwatch')
dynamodb = boto3.client('dynamodb')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_dynamodb_table_names():
    logger.info('Retrieving DynamoDB table names')

    table_listing = dynamodb.list_tables()
    for name in table_listing.get('TableNames', []):
        yield name

    while table_listing.get('LastEvaluatedTableName') is not None:
        last_table_name = table_listing['LastEvaluatedTableName']
        table_listing = dynamodb.list_tables(
            ExclusiveStartTableName=last_table_name
        )

        for name in table_listing.get('TableNames', []):
            yield name

def publish_table_metrics(table_name, table_size, item_count):
    dimensions = [{'Name': 'TableName', 'Value': table_name}]

    now = datetime.datetime.utcnow()
    metrics = [
        {
            'MetricName': 'TableSize',
            'Dimensions': dimensions,
            'Timestamp': now,
            'Value': table_size,
            'Unit': 'Bytes'
        },
        {
            'MetricName': 'ItemCount',
            'Dimensions': dimensions,
            'Timestamp': now,
            'Value': item_count,
            'Unit': 'Count'
        }
    ]

    logger.info(f'Publishing {table_name} table metrics')
    cloudwatch.put_metric_data(
        Namespace=os.environ['METRIC_NAMESPACE'],
        MetricData=metrics
    )

def handler(event, context):
    for table_name in get_dynamodb_table_names():
        try:
            table_description = dynamodb.describe_table(TableName=table_name)
        except ClientError as e:
            err_code = e.response.get('Error', {}).get('Code')
            if err_code == 'ResourceNotFoundException':
                continue
            else:
                raise e

        table_size = table_description['Table']['TableSizeBytes']
        item_count = table_description['Table']['ItemCount']

        publish_table_metrics(table_name, table_size, item_count)
