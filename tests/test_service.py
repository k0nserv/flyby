import pytest
from flyby.service import Service
from operator import itemgetter


def test_service_create(dynamodb):
    response = Service.create({'name': 'foo', 'fqdn': 'foo.example.com'})
    assert response == {
        'name': 'foo',
        'fqdn': 'foo.example.com',
        'healthcheck_path': '/',
        'healthcheck_interval': 5000,
        'healthcheck_rise': 10,
        'healthcheck_fall': 3
    }


def test_service_describe(dynamodb):
    Service.create({'name': 'foo', 'fqdn': 'foo.example.com'})
    Service.register('foo', {'host': '10.0.0.1:80'})
    Service.register('foo', {'host': '10.0.0.2:80'})
    Service.register('foo', {'host': '10.0.0.3:80'})
    assert Service.describe('foo') == {
        'name': 'foo',
        'fqdn': 'foo.example.com',
        'healthcheck_path': '/',
        'healthcheck_interval': 5000,
        'healthcheck_rise': 10,
        'healthcheck_fall': 3,
        'backends': [
            {'host': '10.0.0.1:80'},
            {'host': '10.0.0.2:80'},
            {'host': '10.0.0.3:80'},
        ]
    }


def test_service_query_services(dynamodb):
    foo = Service.create({'name': 'foo', 'fqdn': 'foo.example.com'})
    bar = Service.create({'name': 'bar', 'fqdn': 'bar.example.com'})
    baz = Service.create({'name': 'baz', 'fqdn': 'baz.example.com'})
    assert sorted(Service.query_services(), key=itemgetter('name')) == sorted(
        [foo, bar, baz], key=itemgetter('name'))


def test_service_create_not_valid(dynamodb):
    with pytest.raises(Service.NotValid):
        Service.create({'not': 'valid'})


def test_service_delete(dynamodb):
    Service.create({
        'name': 'foo',
        'fqdn': 'foo.example.com'
    })
    assert Service.delete('foo') is True


def test_service_delete_does_not_exists(dynamodb):
    with pytest.raises(Service.DoesNotExist):
        Service.delete('foo')


def test_service_register(dynamodb):
    Service.create({'name': 'foo', 'fqdn': 'foo.example.com'})
    assert Service.register('foo', {'host': '10.0.0.1:80'}) == {
        'host': '10.0.0.1:80',
    }


def test_service_register_does_not_exists(dynamodb):
    with pytest.raises(Service.DoesNotExist):
        Service.register('foo', {'host': '10.0.0.1:80'})


def test_service_deregister(dynamodb):
    Service.create({'name': 'foo', 'fqdn': 'foo.example.com'})
    Service.register('foo', {'host': '10.0.0.1:80'})
    assert Service.deregister('foo', '10.0.0.1:80') is True


def test_deregister_service_does_not_exists(dynamodb):
    with pytest.raises(Service.DoesNotExist):
        Service.deregister('foo', '10.0.0.1:80')
