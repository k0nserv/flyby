#!/bin/bash

# Foo Resitration
curl -X POST -H "Content-Type: application/json" -d '{"name": "foo", "fqdn": "foo.example.com"}' "http://localhost:5000/service"
curl -X POST -H "Content-Type: application/json" -d '{"service_name": "foo", "target_group_name": "foo-blue", "weight": 50}' "http://localhost:5000/target"
curl -X POST -H "Content-Type: application/json" -d '{"host": "helloworld:80", "service_name": "foo", "target_group_name": "foo-blue"}' "http://localhost:5000/backend"
