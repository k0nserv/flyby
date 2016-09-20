import moto
from flyby.models import ServiceModel
from flyby.models import TargetGroupModel
from flyby.models import BackendModel
from flyby.models import ResolverModel
import pytest


@pytest.yield_fixture
def dynamodb():
    mock = moto.mock_dynamodb2()
    mock.start()
    ServiceModel.create_table(1, 1, True)
    TargetGroupModel.create_table(1, 1, True)
    BackendModel.create_table(1, 1, True)
    ResolverModel.create_table(1, 1, True)
    yield mock
    mock.stop()
