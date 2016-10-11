from flyby.models import Connection
from flyby.cli import ConfigObj, DynamoTableManagement
import pytest


def test_capacity_check(mock_dynamo_call, mocker, mock_config_file):
    dynamo_manager = DynamoTableManagement()
    assert dynamo_manager.capacity_check('service', 'flyby-service', Connection, mock_config_file) == {
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
    mocker.patch('flyby.models.Connection.describe_table', return_value=results)


@pytest.fixture
def mock_config_file(mocker, tmpdir):
    config = tmpdir.join("config.ini")
    config.write(
        """
        [dynamodb]

            [[backend]]
                read_capacity_units = 50
                write_capacity_units = 10

            [[service]]
                read_capacity_units = 5
                write_capacity_units = 2

            [[target-group]]
                read_capacity_units = 10
                write_capacity_units = 2

            [[resolver]]

        """
    )
    config_spec = tmpdir.join("configspec.ini")
    config_spec.write(
        """
        [dynamodb]

            [[backend]]
                read_capacity_units = integer(default=1)
                write_capacity_units = integer(default=1)

            [[service]]
                read_capacity_units = integer(default=1)
                write_capacity_units = integer(default=1)

            [[target-group]]
                read_capacity_units = integer(default=1)
                write_capacity_units = integer(default=1)

            [[resolver]]
                read_capacity_units = integer(default=1)
                write_capacity_units = integer(default=1)

        """
    )
    return ConfigObj(infile=config, configspec=config_spec, stringify=True)
