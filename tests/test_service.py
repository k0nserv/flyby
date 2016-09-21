import pytest
from operator import itemgetter
from flyby.service import TargetGroupModel, BackendModel, Service
import string
import random


def test_service_register_service(dynamodb):
    response = Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    assert response == {
        'name': 'foo',
        'fqdn': 'foo.example.com',
        'healthcheck_path': '/',
        'healthcheck_interval': 5000,
        'healthcheck_rise': 10,
        'healthcheck_fall': 3,
        'failover_pool_fqdn': '',
        'dns_resolver': ''
    }


def test_service_register_service_with_failover(dynamodb):
    response = Service.register_service(
        {
            'name': 'foo',
            'fqdn': 'foo.example.com',
            'failover_pool_fqdn': 'failover.example.com'
        })
    assert response == {
        'name': 'foo',
        'fqdn': 'foo.example.com',
        'healthcheck_path': '/',
        'healthcheck_interval': 5000,
        'healthcheck_rise': 10,
        'healthcheck_fall': 3,
        'failover_pool_fqdn': 'failover.example.com'
    }


def test_service_update_service(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    response = Service.update_service('foo', {
        'failover_pool_fqdn': 'failover.example.com',
        'fqdn': 'newfoo.example.com',
        'healthcheck_path': '/new',
        'healthcheck_interval': 4000,
        'healthcheck_rise': 8,
        'healthcheck_fall': 2
    })
    assert response == {
        'name': 'foo',
        'fqdn': 'newfoo.example.com',
        'healthcheck_path': '/new',
        'healthcheck_interval': 4000,
        'healthcheck_rise': 8,
        'healthcheck_fall': 2,
        'failover_pool_fqdn': 'failover.example.com'
    }


def test_service_register_service_with_failover(dynamodb):
    response = Service.register_service(
        {
            'name': 'foo',
            'fqdn': 'foo.example.com',
            'failover_pool_fqdn': 'failover.example.com:80'
        })
    assert response == {
        'name': 'foo',
        'fqdn': 'foo.example.com',
        'healthcheck_path': '/',
        'healthcheck_interval': 5000,
        'healthcheck_rise': 10,
        'healthcheck_fall': 3,
        'failover_pool_fqdn': 'failover.example.com:80',
        'dns_resolver': ''
    }


def test_service_register_service_with_dns_resolver(dynamodb):
    response = Service.register_service(
        {
            'name': 'foo',
            'fqdn': 'foo.example.com',
            'dns_resolver': 'dnsmasq'
        })
    assert response == {
        'name': 'foo',
        'fqdn': 'foo.example.com',
        'healthcheck_path': '/',
        'healthcheck_interval': 5000,
        'healthcheck_rise': 10,
        'healthcheck_fall': 3,
        'failover_pool_fqdn': '',
        'dns_resolver': 'dnsmasq'
    }


def test_service_update_service(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    response = Service.update_service('foo', {
        'failover_pool_fqdn': 'failover.example.com:80',
        'dns_resolver': 'dnsmasq',
        'fqdn': 'newfoo.example.com',
        'healthcheck_path': '/new',
        'healthcheck_interval': 4000,
        'healthcheck_rise': 8,
        'healthcheck_fall': 2
    })
    assert response == {
        'name': 'foo',
        'fqdn': 'newfoo.example.com',
        'healthcheck_path': '/new',
        'healthcheck_interval': 4000,
        'healthcheck_rise': 8,
        'healthcheck_fall': 2,
        'failover_pool_fqdn': 'failover.example.com:80',
        'dns_resolver': 'dnsmasq'
    }


def test_service_describe(dynamodb):
    Service.register_service({
        'name': 'foo',
        'fqdn': 'foo.example.com',
        'dns_resolver': 'dnsmasq',
        'failover_pool_fqdn': 'failover.example.com:80'
    })
    Service.register_target_group(
        {
            'service_name': 'foo',
            'target_group_name': 'foo-blue',
            'weight': 80
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
            'target_group_name': 'foo-blue'
        }
    )
    Service.register_backend(
        {
            'host': '10.0.0.1:81',
            'service_name': 'foo',
            'target_group_name': 'foo-green'
        }
    )
    Service.register_backend(
        {
            'host': '10.0.0.2:80',
            'service_name': 'foo',
            'target_group_name': 'foo-green'
        }
    )
    assert Service.describe_service('foo') == {
        'name': 'foo',
        'fqdn': 'foo.example.com',
        'healthcheck_path': '/',
        'healthcheck_interval': 5000,
        'healthcheck_rise': 10,
        'healthcheck_fall': 3,
        'failover_pool_fqdn': 'failover.example.com:80',
        'dns_resolver': 'dnsmasq',

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
        [foo, bar, baz], key=itemgetter('name')
        )


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
            'target_group_name': 'foo-blue'
        }
    ) == {
        'host': '10.0.0.1:80'
    }


def test_service_register_backend_allows_dns_for_host(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    Service.register_target_group({'service_name': 'foo', 'target_group_name': 'foo-blue', 'weight': 80})
    host = 'http://nice.example.com:80'
    assert Service.register_backend(
        {
            'host': host,
            'service_name': 'foo',
            'target_group_name': 'foo-blue'
        }
    ) == {
        'host': host
    }


def test_service_register_backend_fails_with_missing_port_in_url(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    with pytest.raises(Service.NotValid) as exec_info:
        Service.register_backend({
            'host': 'http://nice.example.com',
            'service_name': 'foo',
            'target_group_name': 'foo-blue'
        })
    assert 'Host has no port associated' in str(exec_info.value)


def test_service_register_backend_fails_with_negative_port_in_url(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    with pytest.raises(Service.NotValid) as exec_info:
        Service.register_backend({
            'host': 'http://nice.example.com:-1',
            'service_name': 'foo',
            'target_group_name': 'foo-blue'
        })
    assert 'Host has invalid port number' in str(exec_info.value)


def test_service_register_backend_fails_with_large_port_in_url(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    with pytest.raises(Service.NotValid) as exec_info:
        Service.register_backend({
            'host': 'http://nice.example.com:65536',
            'service_name': 'foo',
            'target_group_name': 'foo-blue'
        })
    assert 'Host has invalid port number' in str(exec_info.value)


def test_service_register_backend_fails_with_too_long_url(dynamodb):
    url = "http://{0}".format(''.join([random.choice(string.ascii_lowercase) for n in range(256)]))
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    with pytest.raises(Exception) as exec_info:
        Service.register_backend({
            'host': url + ":80",
            'service_name': 'foo',
            'target_group_name': 'foo-blue'
        })
    assert 'Url is greater than the 255 byte limit' in str(exec_info.value)


def test_service_register_backend_fails_with_long_segment_in_url(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    url = "http://{0}.test.com".format(''.join([random.choice(string.ascii_lowercase) for _ in range(64)]))
    with pytest.raises(Service.NotValid) as exec_info:
        Service.register_backend({
            'host': url + ":80",
            'service_name': 'foo',
            'target_group_name': 'foo-blue'
        })
    assert 'URL segment too long:' in str(exec_info.value)


def test_service_register_does_not_exist(dynamodb):
    with pytest.raises(Service.DoesNotExist):
        Service.register_backend(
            {
                'host': '10.0.0.3:80',
                'service_name': 'foo',
                'target_group_name': 'foo-blue'
            }
        )


def test_service_register_target_group_does_not_exist(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    with pytest.raises(Service.DoesNotExist):
        Service.register_backend(
            {
                'host': '10.0.0.3:80',
                'service_name': 'foo',
                'target_group_name': 'foo-blue'
            }
        )


def test_service_deregister(dynamodb):
    Service.register_service({'name': 'foo', 'fqdn': 'foo.example.com'})
    Service.register_target_group({'service_name': 'foo', 'target_group_name': 'foo-blue', 'weight': 80})
    Service.register_backend(
        {
            'host': '10.0.0.3:80',
            'service_name': 'foo',
            'target_group_name': 'foo-blue'
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


def test_service_register_resolver(dynamodb):
    response = Service.register_resolver({'resolver_name': 'dns', 'nameserver_address': 'dnsmasq'})
    assert response == {
        'hold_valid': '30s',
        'nameserver_address': 'dnsmasq',
        'nameserver_port': 53,
        'resolve_retries': 10,
        'timeout_retry': '5s',
        'name': 'dns'
        }


def test_service_register_resolver_space_in_resolver_name(dynamodb):
    with pytest.raises(Service.NotValid):
        Service.register_resolver({'resolver_name': 'a space', 'nameserver_address': 'dnsmasq'})


def test_deregister_resolver(dynamodb):
    Service.register_resolver({'resolver_name': 'dns', 'nameserver_address': 'dnsmasq'})
    assert Service.deregister_resolver('dns') is True
