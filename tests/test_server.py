from flyby.server import app
from flask import json


def test_server_home():
    response = app.test_client().get('/')
    assert response.status_code == 200
    assert response.data == b'Hello flyby!'


def test_server_register_service(dynamodb):
    response = app.test_client().post(
        '/service',
        data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )
    assert response.status_code == 200
    assert json.loads(response.data)['name'] == 'foo'


def test_server_update_service(dynamodb):
    # Setup service to test update on
    app.test_client().post(
        '/service',
        data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )

    response = app.test_client().put(
        '/service/foo',
        data=json.dumps({'name': 'foo', 'fqdn': 'bar.example.com'})
    )
    assert response.status_code == 200
    assert json.loads(response.data)['fqdn'] == 'bar.example.com'


def test_server_deregister_service(dynamodb):
    app.test_client().post(
        '/service',
        data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )
    response = app.test_client().delete(
        '/service/foo'
    )
    assert response.status_code == 200
    describe_response = app.test_client().get(
        '/service/foo'
    )
    assert describe_response.status_code == 404
    deletion_response = app.test_client().delete(
        '/service/foo'
    )
    assert deletion_response.status_code == 404
    assert deletion_response.data.decode('UTF-8') == 'Service: foo not currently registered with Flyby.'


def test_server_query_services(dynamodb):
    app.test_client().post(
        '/service', data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )
    app.test_client().post(
        '/service', data=json.dumps({'name': 'bar', 'fqdn': 'bar.example.com'})
    )
    response = app.test_client().get('/service')
    assert response.status_code == 200
    services = json.loads(response.data)['services']
    assert len(services) == 2
    assert set([services[0]['name'], services[1]['name']]) == set(['foo', 'bar'])


def test_server_describe_service(dynamodb):
    app.test_client().post(
        '/service',
        data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )
    response = app.test_client().get('/service/foo')
    assert response.status_code == 200
    assert json.loads(response.data)['name'] == 'foo'


def test_server_register_target_group(dynamodb):
    app.test_client().post(
        '/service',
        data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )
    response = app.test_client().post(
        '/target',
        data=json.dumps({'target_group_name': 'foo-blue', 'service_name': 'foo', 'weight': 80})
    )
    assert response.status_code == 200
    assert json.loads(response.data) == {'target_group_name': 'foo-blue', 'weight': 80}


def test_server_deregister_target_group(dynamodb):
    app.test_client().post(
        '/service',
        data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )
    app.test_client().post(
        '/target',
        data=json.dumps(
            {
                'service_name': 'foo',
                'target_group_name': 'foo-blue',
                'weight': 50,
            }
        )
    )
    response = app.test_client().delete('/target/foo/foo-blue')
    assert response.status_code == 200
    service = json.loads(app.test_client().get('/service/foo').data)
    assert service['target_groups'] == []
    second_response = app.test_client().delete('/target/foo/foo-blue')
    assert second_response.status_code == 404
    service = json.loads(app.test_client().get('/service/foo').data)
    assert service['target_groups'] == []


def test_server_register_backend(dynamodb):
    app.test_client().post(
        '/service',
        data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )
    app.test_client().post(
        '/target',
        data=json.dumps({'target_group_name': 'foo-blue', 'service_name': 'foo', 'weight': 80})
    )
    response = app.test_client().post(
        '/backend',
        data=json.dumps(
            {
                'host': '10.0.0.1:80',
                'service_name': 'foo',
                'target_group_name': 'foo-blue',
            }
        )
    )
    assert response.status_code == 200
    assert json.loads(response.data)['host'] == '10.0.0.1:80'


def test_server_deregister_backend(dynamodb):
    app.test_client().post(
        '/service',
        data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )
    app.test_client().post(
        '/target',
        data=json.dumps(
            {
                'service_name': 'foo',
                'target_group_name': 'foo-blue',
                'weight': 50,
            }
        )
    )
    app.test_client().post(
        '/backend',
        data=json.dumps(
            {
                'host': '10.0.0.1:80',
                'service_name': 'foo',
                'target_group_name': 'foo-blue',
            }
        )
    )
    response = app.test_client().delete('/backend/foo/foo-blue/10.0.0.1:80')
    assert response.status_code == 200
    service = json.loads(app.test_client().get('/service/foo').data)
    assert service['target_groups'][0]['backends'] == []
    second_response = app.test_client().delete('/backend/foo/foo-blue/10.0.0.1:80')
    assert second_response.status_code == 404
    service = json.loads(app.test_client().get('/service/foo').data)
    assert service['target_groups'][0]['backends'] == []


def test_server_register_resolver(dynamodb):
    response = app.test_client().post(
        '/resolver',
        data=json.dumps({'resolver_name': 'dns', 'nameserver_address': 'dnsmasq'})
    )
    assert response.status_code == 200
    assert json.loads(response.data)['name'] == 'dns'
    assert json.loads(response.data)['nameserver_address'] == 'dnsmasq'


def test_server_describe_resolver(dynamodb):
    app.test_client().post(
        '/resolver',
        data=json.dumps({'resolver_name': 'dns', 'nameserver_address': 'dnsmasq'})
    )
    response = app.test_client().get('/resolver/dns')
    assert response.status_code == 200
    assert json.loads(response.data)['name'] == 'dns'
    assert json.loads(response.data)['nameserver_address'] == 'dnsmasq'


def test_server_deregister_resolver(dynamodb):
    app.test_client().post(
        '/resolver',
        data=json.dumps({'resolver_name': 'dns', 'nameserver_address': 'dnsmasq'})
    )
    response = app.test_client().delete('/resolver/dns')
    assert response.status_code == 200

    describe_response = app.test_client().get('/resolver/dns')
    assert describe_response.status_code == 404

    deletion_response = app.test_client().delete('/resolver/dns')
    assert deletion_response.status_code == 404
    assert deletion_response.data.decode('UTF-8') == 'Resolver: dns not currently registered with Flyby.'
