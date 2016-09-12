#!/bin/bash

# Foo Resitration
curl -X POST -H "Content-Type: application/json" -d '{"name": "foo", "fqdn": "foo.example.com", "failover_pool_fqdn": "bar:80", "healthcheck_interval": 1000}' "http://localhost:5000/service"
curl -X POST -H "Content-Type: application/json" -d '{"service_name": "foo", "target_group_name": "backend", "weight": 50}' "http://localhost:5000/target"
curl -X POST -H "Content-Type: application/json" -d '{"host": "foo:80", "service_name": "foo", "target_group_name": "backend"}' "http://localhost:5000/backend"
