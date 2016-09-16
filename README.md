[![Build Status](https://travis-ci.org/Skyscanner/flyby.svg?branch=master)](https://travis-ci.org/Skyscanner/flyby)
[![](https://images.microbadger.com/badges/image/skyscanner/flyby.svg)](http://microbadger.com/images/skyscanner/flyby "Get your own image badge on microbadger.com")
[![](https://images.microbadger.com/badges/version/skyscanner/flyby.svg)](http://microbadger.com/images/skyscanner/flyby "Get your own version badge on microbadger.com")

# Flyby
Flyby is a simple distributed HAProxy layer used for load balancing our ECS shared cluster.

Flyby implements a simple distributed HaProxy layer configured via API.

Every minute the load balancer syncs-up and refreshes its configuration when needed.

# Demo
*Note:* These commands assume you are using a docker-machine environment on `192.168.99.100`, you may need to update the IP address curl-ed to.

This docker-compose demo uses [DynamoDBLocal](http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html) for mocking DynamoDB, however it is possible to use other backends such as [moto](https://github.com/spulec/moto) locally.

This is a simple scenario of registering a foo example service
```
## Start server with a dynamodb local server and a local service
docker-compose up

## Register a new service foo
curl -X POST -H "Content-Type: application/json" -d '{
    "name": "foo",
    "fqdn": "foo.example.com"
}
' "http://192.168.99.100:5000/service"

## Register a new target group 'foo-blue'
curl -X POST -H "Content-Type: application/json" -d '{
    "service_name": "foo",
    "target_group_name": "foo-blue",
    "weight": 50
}
' "http://192.168.99.100:5000/target"

## Register a new backend
curl -X POST -H "Content-Type: application/json" -d '{
    "host": "192.168.99.100:9000",
    "service_name": "foo",
    "target_group_name": "foo-blue"
}
' "http://192.168.99.100:5000/backend"

## Check the data
curl -X GET "http://192.168.99.100:5000/service"
curl -X GET "http://192.168.99.100:5000/haproxy/config"
```

# Local Failover Testing

A Docker compose file `docker-compose-local-failover-test.yml` is provided which will set up an environment with 2 backends: foo and bar.
run the script `setup_test_foo.sh` after your docker compose has finished to provision the configuration.
add a host entry for foo.example.com to localhost and you should be able to test failover.
