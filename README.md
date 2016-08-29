[![Build Status](https://travis-ci.org/Skyscanner/flyby.svg?branch=master)](https://travis-ci.org/Skyscanner/flyby)
[![](https://images.microbadger.com/badges/image/skyscanner/flyby.svg)](http://microbadger.com/images/skyscanner/flyby "Get your own image badge on microbadger.com")
[![](https://images.microbadger.com/badges/version/skyscanner/flyby.svg)](http://microbadger.com/images/skyscanner/flyby "Get your own version badge on microbadger.com")

# Flyby
Flyby is a simple distributed HAProxy layer used for load balancing our ECS shared cluster.

Flyby implements a simple distributed HaProxy layer configured via API.

Every minute the load balancer syncs-up and refreshes its configuration when needed.

Demo
====

This is a simple scenario of registering a foo example service
```
# Start server with a mocked dynamodb server
docker-compose up

# Start an example container
docker run -e NAME=foo -d -p 9000:80 tutum/hello-world

# Register a new service foo

curl -X POST -H "Content-Type: application/json" -d '{
    "name": "foo",
    "fqdn": "foo.example.com"
}
' "http://192.168.99.100:5000/service"

# Register a new backend
curl -X POST -H "Content-Type: application/json" -d '{
    "host": "192.168.99.100:9000"
}
' "http://192.168.99.100:5000/service/foo/register"

# Check the data
curl -X GET "http://192.168.99.100:5000/service"
curl -X GET "http://192.168.99.100:5000/haproxy/config"
```
