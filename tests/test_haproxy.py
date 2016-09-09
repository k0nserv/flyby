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
            'target_groups': [
                {
                    "target_group_name": "foo-blue",
                    "weight": 80,
                    "backends": [
                        {'host': '10.0.0.1:80', 'is_failover': "false"},
                        {'host': '10.0.0.2:80', 'is_failover': "false"},
                        {'host': '10.0.0.3:80', 'is_failover': "false"}
                    ]
                },
                {
                    "target_group_name": "foo-green",
                    "weight": 20,
                    "backends": [
                        {'host': '10.0.0.1:81', 'is_failover': "false"},
                        {'host': '10.0.0.2:81', 'is_failover': "false"},
                        {'host': '10.0.0.3:81', 'is_failover': "false"}
                    ]
                },
            ]
        }
    ])
    updated_config = config.read()
    assert 'acl foo-aclrule hdr(host) foo.example.com' in updated_config
    assert 'use_backend foo-cluster if foo-aclrule' in updated_config
    assert "backend foo-cluster" in updated_config
    assert "server foo-foo-blue1 10.0.0.1:80 check inter 10s weight 80" in updated_config
    assert "server foo-foo-green2 10.0.0.2:81 check inter 10s weight 20" in updated_config
    assert "server foo-foo-green3 10.0.0.3:81 check inter 10s weight 20" in updated_config
