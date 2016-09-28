#!/bin/bash

# resolver Registration
curl -X POST -H "Content-Type: application/json" -d '{"resolver_name": "dnsmasq", "nameserver_address": "dnsmasq"}' "http://localhost:5000/resolver"

# foo.example.com with default to 'foo' and failover to HTTPS backup 'bar'
curl -X POST -H "Content-Type: application/json" -d '{"name": "foo", "fqdn": "foo.example.com", "failover_pool_fqdn": "bar:80", "healthcheck_interval": 1000, "dns_resolver": "dnsmasq"}' "http://localhost:5000/service"
curl -X POST -H "Content-Type: application/json" -d '{"service_name": "foo", "target_group_name": "backend", "weight": 50}' "http://localhost:5000/target"
curl -X POST -H "Content-Type: application/json" -d '{"host": "foo:80", "service_name": "foo", "target_group_name": "backend"}' "http://localhost:5000/backend"