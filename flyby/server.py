from flyby.service import Service
from flyby.haproxy import Haproxy
import flask


app = flask.Flask(__name__)


@app.route("/")
def home():
    return "Hello flyby!"


@app.route("/service", methods=['POST'])
def create_service():
    data = Service.create(flask.request.get_json(force=True))
    return flask.jsonify(data)


@app.route("/service", methods=['GET'])
def query_services():
    return flask.jsonify({'services': Service.query_services()})


@app.route("/service/<service_name>", methods=['GET'])
def describe_service(service_name):
    return flask.jsonify(Service.describe(service_name))


@app.route("/service/<service_name>/register", methods=['POST'])
def register_backend(service_name):
    data = Service.register(service_name, flask.request.get_json(force=True))
    return flask.jsonify(data)


@app.route("/service/<service_name>/<host>", methods=['DELETE'])
def deregister_backend(service_name, host):
    Service.deregister(service_name, host)
    return 'OK'


@app.route("/service/<service_name>", methods=['DELETE'])
def delete_service(service_name):
    Service.delete(service_name)
    return 'OK'


@app.route("/haproxy/config", methods=['GET'])
def haproxy_config():
    return flask.Response(Haproxy().config, mimetype='application/txt')
