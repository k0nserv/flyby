from validator import Required
from validator import Pattern
from validator import Length
from validator import Range
from validator import validate
from flyby.models import ServiceModel
from flyby.models import ServiceBackendModel
from operator import itemgetter


class Service:

    class NotValid(Exception):
        pass

    class DoesNotExist(Exception):
        pass

    @classmethod
    def create(cls, service_def):
        valid, errors = cls.validate_service(service_def)
        if not valid:
            raise cls.NotValid(errors)
        service = ServiceModel(**service_def)
        service.save()
        return service.as_dict()

    @classmethod
    def describe(cls, service_name):
        try:
            service = ServiceModel.get(service_name)
        except ServiceModel.DoesNotExist:
            raise Service.DoesNotExist(service_name)
        backends = ServiceBackendModel.scan(service_name__eq=service_name)
        data = service.as_dict()
        data['backends'] = sorted([b.as_dict() for b in backends], key=itemgetter('host'))
        return data

    @classmethod
    def query_services(cls):
        data = {s.name: s.as_dict() for s in ServiceModel.scan()}
        for backend in ServiceBackendModel.scan():
            data[backend.service_name]['backends'] = data[backend.service_name].get('backends', [])
            data[backend.service_name]['backends'].append(backend.as_dict())
        return list(data.values())

    @classmethod
    def delete(cls, name):
        try:
            service = ServiceModel.get(name)
        except ServiceModel.DoesNotExist:
            raise Service.DoesNotExist(name)
        service.delete()
        return True

    @classmethod
    def register(cls, service_name, backend_definition):
        valid, errors = cls.validate_backend(backend_definition)
        if not valid:
            raise cls.NotValid(errors)
        try:
            ServiceModel.get(service_name)
        except ServiceModel.DoesNotExist:
            raise Service.DoesNotExist(service_name)
        backend = ServiceBackendModel(
            service_name=service_name,
            **backend_definition
        )
        backend.save()
        return backend.as_dict()

    @classmethod
    def deregister(cls, service_name, host):
        try:
            backend = ServiceBackendModel.get(service_name, host)
        except ServiceBackendModel.DoesNotExist:
            raise Service.DoesNotExist("{} - {}".format(service_name, host))
        backend.delete()
        return True

    @classmethod
    def validate_service(cls, data):
        rules = {
            "name": [Required, Length(3, 25)],
            "fqdn": [Required],
            "healthcheck_path": [],
            "healthcheck_interval": [Range(1000, 60000)],
            "healthcheck_rise": [Range(0, 20)],
            "healthcheck_fall": [Range(0, 20)],
        }
        return validate(rules, data)

    @classmethod
    def validate_backend(cls, data):
        rules = {
            "host": [Required, Pattern('\d+.\d+.\d+.\d+:\d+')],
        }
        return validate(rules, data)
