import pytest
from flyby.service import Service
from operator import itemgetter
from flyby.service import TargetGroupModel, BackendModel


def test_service_register_service(dynamodb):
    response = Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    assert response == {
        'name': 'foo',
        'fqdn': 'foo.example.com',
        'healthcheck_path': '/',
        'healthcheck_interval': 5000,
        'healthcheck_rise': 10,
        'healthcheck_fall': 3
    }


def test_service_describe(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    Service.register_target_group(
        {
            'service_name': 'foo',
            'target_group_name': 'foo-blue',
            'weight': 80,
        }
    )
    Service.register_target_group(
        {
            'service_name': "foo",
            "target_group_name": "foo-green",
            "weight": 40
        }
    )
    Service.register_backend(
        {
            'host': '10.0.0.1:80',
            'service_name': 'foo',
            'target_group_name': 'foo-blue',
        }
    )
    Service.register_backend(
        {
            'host': '10.0.0.1:81',
            'service_name': 'foo',
            'target_group_name': 'foo-green',
        }
    )
    Service.register_backend(
        {
            'host': '10.0.0.2:80',
            'service_name': 'foo',
            'target_group_name': 'foo-green',
        }
    )
    assert Service.describe_service('foo') == {
        'name': 'foo',
        'fqdn': 'foo.example.com',
        'healthcheck_path': '/',
        'healthcheck_interval': 5000,
        'healthcheck_rise': 10,
        'healthcheck_fall': 3,
        'target_groups': [
            {
                "target_group_name": "foo-blue",
                "backends": [
                    {
                        "host": '10.0.0.1:80'
                    }
                ],
                "weight": 80
            },
            {
                "target_group_name": "foo-green",
                "backends": [
                    {
                        "host": "10.0.0.1:81"
                    },
                    {
                        "host": "10.0.0.2:80"
                    }
                ],
                "weight": 40
            },
        ]
    }


def test_service_query_services(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    Service.register_target_group({'service_name': 'foo', 'target_group_name': 'foo-blue', 'weight': 80})
    Service.register_target_group({'service_name': 'foo', 'target_group_name': 'foo-green', 'weight': 20})
    Service.register_backend({'service_name': 'foo', 'target_group_name': 'foo-blue', 'host': '10.0.0.1:80'})
    Service.register_backend({'service_name': 'foo', 'target_group_name': 'foo-blue', 'host': '10.0.0.2:80'})
    Service.register_backend({'service_name': 'foo', 'target_group_name': 'foo-blue', 'host': '10.0.0.3:80'})
    Service.register_backend({'service_name': 'foo', 'target_group_name': 'foo-green', 'host': '10.0.0.1:81'})
    foo = Service.describe_service('foo')
    bar = Service.register_service({'name': 'bar', 'fqdn': 'bar.example.com'})
    baz = Service.register_service({'name': 'baz', 'fqdn': 'baz.example.com'})
    assert sorted(Service.query_services(), key=itemgetter('name')) == sorted(
        [foo, bar, baz], key=itemgetter('name'))


def test_service_create_not_valid(dynamodb):
    with pytest.raises(Service.NotValid):
        Service.register_service({'not': 'valid'})


def test_service_delete(dynamodb):
    Service.register_service({
        'name': 'foo',
        'fqdn': 'foo.example.com'
    })
    assert Service.deregister_service('foo') is True


def test_service_delete_does_not_exist(dynamodb):
    with pytest.raises(Service.DoesNotExist):
        Service.deregister_service('foo')


def test_service_register_target_group(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    assert Service.register_target_group(
        {
            'service_name': 'foo',
            'target_group_name': 'foo-blue',
            'weight': 50,
        },
    ) == {
               'target_group_name': 'foo-blue',
               'weight': 50,
           }


def test_service_deregister_target_group(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    Service.register_target_group(
        {
            'service_name': 'foo',
            'target_group_name': 'foo-blue',
            'weight': 50,
        },
    )
    assert Service.deregister_target_group(
        service_name='foo',
        target_group_name='foo-blue'
    )


def test_service_register_target_group_service_does_not_exist(dynamodb):
    with pytest.raises(Service.DoesNotExist):
        Service.register_target_group(
            {
                'service_name': 'foo',
                'target_group_name': 'foo-blue',
                'weight': 50,
            }
        )


def test_service_register_backend(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    Service.register_target_group({'service_name': 'foo', 'target_group_name': 'foo-blue', 'weight': 80})
    assert Service.register_backend(
        {
            'host': '10.0.0.1:80',
            'service_name': 'foo',
            'target_group_name': 'foo-blue',
        }
    ) == {
               'host': '10.0.0.1:80',
           }


def test_service_register_does_not_exist(dynamodb):
    with pytest.raises(Service.DoesNotExist):
        Service.register_backend(
            {
                'host': '10.0.0.3:80',
                'service_name': 'foo',
                'target_group_name': 'foo-blue',
            }
        )


def test_service_register_target_group_does_not_exist(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    with pytest.raises(Service.DoesNotExist):
        Service.register_backend(
            {
                'host': '10.0.0.3:80',
                'service_name': 'foo',
                'target_group_name': 'foo-blue',
            }
        )


def test_service_deregister(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    Service.register_target_group({'service_name': 'foo', 'target_group_name': 'foo-blue', 'weight': 80})
    Service.register_backend(
        {
            'host': '10.0.0.3:80',
            'service_name': 'foo',
            'target_group_name': 'foo-blue',
        }
    )
    service_description = Service.describe_service('foo')
    print(service_description)
    assert Service.deregister_service('foo') is True
    with pytest.raises(TargetGroupModel.DoesNotExist):
        TargetGroupModel.get('foo', 'foo-blue')
    with pytest.raises(BackendModel.DoesNotExist):
        BackendModel.get('foo', '10.0.0.3:80')


def test_deregister_service_does_not_exist(dynamodb):
    with pytest.raises(Service.DoesNotExist):
        Service.deregister_service('foo')
