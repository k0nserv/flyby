from flyby.haproxy import Haproxy


def test_harproxy_update_config(tmpdir, mocker):
    mocker.patch('flyby.haproxy.subprocess')
    config = tmpdir.join("haproxy.cfg")
    config.write("ha config")
    ha = Haproxy(config_path=str(config))
    ha.update([
        {
            'name': 'foo',
            'fqdn': 'foo.example.com',
            'healthcheck_path': '/',
            'healthcheck_interval': 10,
            'healthcheck_rise': 10,
            'healthcheck_fall': 3,
            'backends': [
                {'host': '10.0.0.1:80'},
                {'host': '10.0.0.2:80'},
                {'host': '10.0.0.3:80'}
            ]
        }
    ])
    updated_config = config.read()
    assert 'acl foo-aclrule hdr(host) foo.example.com' in updated_config
    assert 'use_backend foo-cluster if foo-aclrule' in updated_config
    assert "backend foo-cluster" in updated_config
    assert "server foo1 10.0.0.1:80" in updated_config
    assert "server foo2 10.0.0.2:80" in updated_config
    assert "server foo3 10.0.0.3:80" in updated_config
