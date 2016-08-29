from flyby.server import app
from flask import json


def test_server_home():
    response = app.test_client().get('/')
    assert response.status_code == 200
    assert response.data == b'Hello flyby!'


def test_server_create(dynamodb):
    response = app.test_client().post(
        '/service',
        data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )
    assert response.status_code == 200
    assert json.loads(response.data)['name'] == 'foo'


def test_server_query(dynamodb):
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


def test_server_describe(dynamodb):
    app.test_client().post(
        '/service',
        data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )
    response = app.test_client().get('/service/foo')
    assert response.status_code == 200
    assert json.loads(response.data)['name'] == 'foo'


def test_server_register(dynamodb):
    app.test_client().post(
        '/service',
        data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )
    response = app.test_client().post(
        '/service/foo/register',
        data=json.dumps({'host': '10.0.0.1:80'})
    )
    assert response.status_code == 200
    print(json.loads(response.data))
    assert json.loads(response.data)['host'] == '10.0.0.1:80'


def test_server_deregister(dynamodb):
    app.test_client().post(
        '/service',
        data=json.dumps({'name': 'foo', 'fqdn': 'foo.example.com'})
    )
    app.test_client().post(
        '/service/foo/register',
        data=json.dumps({'host': '10.0.0.1:80'})
    )

    response = app.test_client().delete('/service/foo/10.0.0.1:80')
    assert response.status_code == 200
    service = json.loads(app.test_client().get('/service/foo').data)
    assert service['backends'] == []
