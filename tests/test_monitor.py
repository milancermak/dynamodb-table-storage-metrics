from unittest.mock import Mock

from botocore.exceptions import ClientError
import boto3
import pytest

from monitor import main

# @pytest.fixture(autouse=True):
# def setup_env(monkeypatch):
#     monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')


def test_get_dynamodb_table_names(monkeypatch):
    first_listing = {
        'TableNames': ['one-table', 'two-table'],
        'LastEvaluatedTableName': 'two-table'
    }
    second_listing = {
        'TableNames': ['three-table']
    }
    mock_list = Mock(side_effect=[first_listing, second_listing])
    monkeypatch.setattr('monitor.main.dynamodb.list_tables', mock_list)

    table_names = list(main.get_dynamodb_table_names())

    assert table_names == ['one-table', 'two-table', 'three-table']

def test_publish_table_metrics(monkeypatch):
    monkeypatch.setenv('METRIC_NAMESPACE', 'test-metric')
    mock_put = Mock()
    monkeypatch.setattr('monitor.main.cloudwatch.put_metric_data', mock_put)

    main.publish_table_metrics('foo-table', 1450, 90)

    mock_put.assert_called_once()
    kwargs = mock_put.call_args[1]
    assert kwargs['Namespace'] == 'test-metric'

    metric_data = kwargs['MetricData']
    assert len(metric_data) == 2

    table_size_metric = metric_data[0]
    assert table_size_metric['Value'] == 1450
    assert table_size_metric['Unit'] == 'Bytes'

    item_count_metric = metric_data[1]
    assert item_count_metric['Value'] == 90
    assert item_count_metric['Unit'] == 'Count'

    dimensions = table_size_metric['Dimensions']
    assert dimensions[0] == {'Name': 'TableName', 'Value': 'foo-table'}

def test_handler(monkeypatch):
    mock_get = Mock(side_effect=[('foo-table', 'bar-table')])
    monkeypatch.setattr('monitor.main.get_dynamodb_table_names', mock_get)

    table_description = {
        'Table': {
            'TableSizeBytes': 1450,
            'ItemCount': 90
        }
    }
    no_resource = ClientError({'Error': {'Code': 'ResourceNotFoundException'}},
                              'test')
    mock_describe = Mock(side_effect=[table_description, no_resource])
    monkeypatch.setattr('monitor.main.dynamodb.describe_table', mock_describe)

    mock_publish = Mock()
    monkeypatch.setattr('monitor.main.publish_table_metrics', mock_publish)

    main.handler({}, {})

    mock_get.assert_called_once()
    assert mock_describe.call_count == 2
    mock_publish.assert_called_once()

    table_name, table_size, item_count = mock_publish.call_args[0]
    assert table_name == 'foo-table'
    assert table_size == 1450
    assert item_count == 90
