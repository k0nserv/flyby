import moto
from flyby.models import ServiceModel
from flyby.models import TargetGroupModel
from flyby.models import BackendModel
from flyby.utils import NTP
import pytest
from datetime import datetime


class DynamoHandler(object):
    def __init__(self):
        self.mock = moto.mock_dynamodb2()

    def __enter__(self):
        self.mock.start()
        ServiceModel.create_table(1, 1, True)
        TargetGroupModel.create_table(1, 1, True)
        BackendModel.create_table(1, 1, True)
        self._server_time_getter = NTP.get_server_time
        NTP.get_server_time = datetime.now
        return self

    def __exit__(self, *args, **kwargs):
        NTP.get_server_time = self._server_time_getter
        self.mock.stop()


@pytest.yield_fixture
def dynamodb():
    with DynamoHandler() as dynamo:
        yield dynamo


@pytest.fixture
def get_dynamodb():
    return DynamoHandler
