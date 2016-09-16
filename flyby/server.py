from flyby.service import Service
from flyby.haproxy import Haproxy
import flask


app = flask.Flask(__name__)


@app.route("/")
def home():
    return "Hello flyby!"


@app.route("/service", methods=['POST'])
def register_service():
    data = Service.register_service(flask.request.get_json(force=True))
    return flask.jsonify(data)


@app.route("/service/<service_name>", methods=['PUT'])
def update_service(service_name):
    try:
        data = Service.update_service(service_name, flask.request.get_json(force=True))
        return flask.jsonify(data)
    except Service.DoesNotExist:
        return 'Service: {} not currently registered with Flyby.'.format(service_name), 404


@app.route("/service/<service_name>", methods=['DELETE'])
def deregister_service(service_name):
    try:
        Service.deregister_service(service_name)
    except Service.DoesNotExist:
        return 'Service: {} not currently registered with Flyby.'.format(service_name), 404
    return 'OK'


@app.route("/service", methods=['GET'])
def query_services():
    return flask.jsonify({'services': Service.query_services()})


@app.route("/service/<service_name>", methods=['GET'])
def describe_service(service_name):
    try:
        return flask.jsonify(Service.describe_service(service_name))
    except Service.DoesNotExist:
        return 'Service: {} not currently registered with Flyby.'.format(service_name), 404


@app.route("/target", methods=['POST'])
def register_target_group():
    try:
        return flask.jsonify(Service.register_target_group(flask.request.get_json(force=True)))
    except Service.DoesNotExist as e:
        return 'Service: {} not currently registered with Flyby.'.format(e.args[0]), 404


@app.route("/target/<service_name>/<target_group_name>", methods=['DELETE'])
def delete_service(service_name, target_group_name):
    try:
        Service.deregister_target_group(service_name, target_group_name)
    except Service.DoesNotExist:
        return 'Target group: {} for service: {} not currently registered with Flyby.'.format(target_group_name,
                                                                                              service_name), 404
    return 'OK'


@app.route("/backend", methods=['POST'])
def register_backend():
    try:
        return flask.jsonify(Service.register_backend(flask.request.get_json(force=True)))
    except Service.DoesNotExist as e:
        return "{} does not exist.".format(e.args[0]), 404


@app.route("/backend/<service_name>/<target_group_name>/<host>", methods=['DELETE'])
def deregister_backend(service_name, target_group_name, host):
    try:
        Service.deregister_backend(service_name, target_group_name, host)
    except Service.DoesNotExist:
        return 'Backend: {} for target group: {} in service: {}' \
               ' not currently registered with Flyby.'.format(host, target_group_name, service_name), 404
    return 'OK'


@app.route("/haproxy/config", methods=['GET'])
def haproxy_config():
    return flask.Response(Haproxy().config, mimetype='application/txt')
