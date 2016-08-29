import moto
from flyby.models import ServiceModel
from flyby.models import ServiceBackendModel
import pytest
import sys
try:
    import tendo.ansiterm
except:
    pass


@pytest.yield_fixture
def dynamodb():
    mock = moto.mock_dynamodb2()
    mock.start()
    ServiceModel.create_table(1, 1, True)
    ServiceBackendModel.create_table(1, 1, True)
    yield mock
    mock.stop()
