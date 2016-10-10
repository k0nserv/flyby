from flyby.cli import Connection
from flyby.models import ConfigObj, DynamoCapacityManagement
import pytest


def test_capacity_check(mock_dynamo_call, mocker, mock_config_file):
    dynamo_manager = DynamoCapacityManagement()
    assert dynamo_manager.capacity_check('service', 'flyby-service', Connection) == {
        'decreases': 0,
        'read': 5,
        'result': False,
        'write': 2
    }


@pytest.fixture
def mock_dynamo_call(mocker):
    results = {
        'AttributeDefinitions': [{'AttributeName': 'name', 'AttributeType': 'S'}],
        'CreationDateTime': 1475771801.062498,
        'GlobalSecondaryIndexes': [],
        'ItemCount': 0,
        'KeySchema': [{'AttributeName': 'name', 'KeyType': 'HASH'}],
        'LocalSecondaryIndexes': [],
        'ProvisionedThroughput': {
            'NumberOfDecreasesToday': 0,
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1
                                  },
        'TableName': 'flyby-service',
        'TableSizeBytes': 0,
        'TableStatus': 'ACTIVE'
    }
    mocker.patch('flyby.cli.Connection.describe_table', return_value=results)


@pytest.fixture
def mock_config_file(mocker, tmpdir):
    config = tmpdir.join("config.ini")
    config.write(
        """
        [dynamodb]

            [[backend]]
                ReadCapacityUnits = 50
                WriteCapacityUnits = 10

            [[service]]
                ReadCapacityUnits = 5
                WriteCapacityUnits = 2

            [[target-group]]
                ReadCapacityUnits = 10
                WriteCapacityUnits = 2

            [[resolver]]

        """
    )
    config_spec = tmpdir.join("configspec.ini")
    config_spec.write(
        """
        [dynamodb]

            [[backend]]
                ReadCapacityUnits = integer(default=1)
                WriteCapacityUnits = integer(default=1)

            [[service]]
                ReadCapacityUnits = integer(default=1)
                WriteCapacityUnits = integer(default=1)

            [[target-group]]
                ReadCapacityUnits = integer(default=1)
                WriteCapacityUnits = integer(default=1)

            [[resolver]]
                ReadCapacityUnits = integer(default=1)
                WriteCapacityUnits = integer(default=1)

        """
    )
    sample_config = ConfigObj(infile=config, configspec=config_spec, stringify=True)
    mocker.patch('flyby.models.ConfigObj', return_value=sample_config)
