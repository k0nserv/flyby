from flyby.haproxy import Haproxy


def test_haproxy_update_config(tmpdir, mocker):
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
                        {'host': '10.0.0.1:80', 'status': 'HEALTHY'},
                        {'host': '10.0.0.2:80', 'status': 'UNHEALTHY'},
                        {'host': '10.0.0.3:80', 'status': 'HEALTHY'}
                    ]
                },
                {
                    "target_group_name": "foo-green",
                    "weight": 20,
                    "backends": [
                        {'host': '10.0.0.1:81', 'status': 'HEALTHY'},
                        {'host': '10.0.0.2:81', 'status': 'HEALTHY'},
                        {'host': '10.0.0.3:81', 'status': 'HEALTHY'}
                    ]
                },
            ]
        }
    ])
    updated_config = config.read()
    print(updated_config)
    assert 'acl foo-aclrule hdr(host) foo.example.com' in updated_config
    assert 'use_backend foo-backend if foo-aclrule' in updated_config
    assert "backend foo-backend" in updated_config
    assert "server foo-foo-blue-1 10.0.0.1:80 check inter 10s weight 256" in updated_config
    assert "server foo-foo-blue-1 10.0.0.2:80 check inter 10s weight 256" not in updated_config
    assert "server foo-foo-green-2 10.0.0.2:81 check inter 10s weight 43" in updated_config
    assert "server foo-foo-green-3 10.0.0.3:81 check inter 10s weight 43" in updated_config


def test_haproxy_update_config_supports_resolver(tmpdir, mocker):
    mocker.patch('flyby.haproxy.subprocess')
    config = tmpdir.join("haproxy.cfg")
    config.write("ha config")
    ha = Haproxy(config_path=str(config))
    resolvers = [
        {
            'name': 'my-resolver',
            'nameserver_address': 'dnsmasq',
            'nameserver_port': '9053',
            'resolve_retries': '7',
            'timeout_retry': '10',
            'hold_valid': '42'
        }
    ]
    services = [
        {
            'name': 'foo',
            'fqdn': 'foo.example.com',
            'healthcheck_path': '/',
            'healthcheck_interval': 10,
            'healthcheck_rise': 10,
            'healthcheck_fall': 3,
            'dns_resolver': 'my-resolver',
            'target_groups': [
                {
                    "target_group_name": "foo-blue",
                    "weight": 100,
                    "backends": [
                        {'host': '10.0.0.1:80', 'status': 'HEALTHY'}
                    ]
                }
            ]
        }
    ]
    ha.update(services=services, resolvers=resolvers)
    updated_config = config.read()
    assert "resolvers my-resolver" in updated_config
    assert "nameserver            nameserver dnsmasq:9053" in updated_config
    assert "resolve_retries       7" in updated_config
    assert "timeout retry         10" in updated_config
    assert "hold valid            42" in updated_config
    assert "server foo-foo-blue-1 10.0.0.1:80 check inter 10s weight 256  resolvers my-resolver" in updated_config


def test_haproxy_update_config_does_not_inject_unneeded_resolver(tmpdir, mocker):
    mocker.patch('flyby.haproxy.subprocess')
    config = tmpdir.join("haproxy.cfg")
    config.write("ha config")
    ha = Haproxy(config_path=str(config))

    services = [
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
                    "weight": 100,
                    "backends": [
                        {'host': '10.0.0.1:80', 'status': 'HEALTHY'}
                    ]
                }
            ]
        }
    ]
    ha.update(services=services)
    updated_config = config.read()
    print(updated_config)
    assert "resolvers" not in updated_config


def test_haproxy_update_config_supports_ssl_backend_failover(tmpdir, mocker):
    mocker.patch('flyby.haproxy.subprocess')
    config = tmpdir.join("haproxy.cfg")
    config.write("ha config")
    ha = Haproxy(config_path=str(config))
    services = [
        {
            'name': 'foo',
            'fqdn': 'foo.example.com',
            'failover_pool_fqdn': 'bar.example.com',
            'failover_pool_use_https': 1,
            'healthcheck_path': '/',
            'healthcheck_interval': 10,
            'healthcheck_rise': 10,
            'healthcheck_fall': 3,
            'target_groups': [
                {
                    "target_group_name": "foo-blue",
                    "weight": 100,
                    "backends": [
                        {'host': '10.0.0.1:80', 'status': 'HEALTHY'}
                    ]
                }
            ]
        }
    ]
    ha.update(services=services)
    updated_config = config.read()
    assert "ca-base      /etc/ssl/certs" in updated_config
    assert "option httpchk GET / HTTP/1.1\\r\\nHost:\ foo.example.com" in updated_config
    assert "http-request set-header X-Forwarded-Proto https" in updated_config
    assert "server foo-foo-blue-backup bar.example.com backup check inter 10s   ssl ca-file ca-certificates.crt"\
           in updated_config


def test_haproxy_update_config_supports_ssl_backend_failover_with_self_signed_cert(tmpdir, mocker):
    mocker.patch('flyby.haproxy.subprocess')
    config = tmpdir.join("haproxy.cfg")
    config.write("ha config")
    ha = Haproxy(config_path=str(config))
    services = [
        {
            'name': 'foo',
            'fqdn': 'foo.example.com',
            'failover_pool_fqdn': 'bar.example.com',
            'failover_pool_use_https': 1,
            'failover_pool_ssl_allow_self_signed_certs': 1,
            'healthcheck_path': '/',
            'healthcheck_interval': 10,
            'healthcheck_rise': 10,
            'healthcheck_fall': 3,
            'target_groups': [
                {
                    "target_group_name": "foo-blue",
                    "weight": 100,
                    "backends": [
                        {'host': '10.0.0.1:80', 'status': "HEALTHY"}
                    ]
                }
            ]
        }
    ]
    ha.update(services=services)
    updated_config = config.read()
    assert "server foo-foo-blue-backup bar.example.com backup check inter 10s   ssl ca-file ca-certificates.crt   " \
           "verify none" in updated_config
