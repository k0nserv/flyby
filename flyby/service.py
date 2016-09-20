from flyby.utils import ValidHost, ValidHostWithPort
from validator import Required, Pattern
from validator import Length
from validator import Range
from validator import validate
from flyby.models import ServiceModel
from flyby.models import BackendModel
from flyby.models import ResolverModel
from flyby.models import TargetGroupModel
from operator import itemgetter


class Service:

    class NotValid(Exception):
        pass

    class DoesNotExist(Exception):
        pass

    @classmethod
    def register_service(cls, service_def):
        valid, errors = cls.validate_service(service_def)
        if not valid:
            raise cls.NotValid(errors)
        service = ServiceModel(**service_def)
        service.save()
        return service.as_dict()

    @classmethod
    def update_service(cls, service_name, update_def):

        try:
            service = ServiceModel.get(service_name)
        except ServiceModel.DoesNotExist:
            raise Service.DoesNotExist(service_name)

        for k, v in update_def.items():
            if k in service.attribute_values.keys():
                service.attribute_values[k] = v

        service_dict = service.as_dict()
        valid, errors = cls.validate_service(service_dict)
        if not valid:
            raise cls.NotValid(errors)

        service.save()
        return service.as_dict()

    @classmethod
    def deregister_service(cls, name):
        try:
            service = ServiceModel.get(name)
        except ServiceModel.DoesNotExist:
            raise Service.DoesNotExist(name)
        service_description = cls.describe_service(name)
        for target_group in service_description['target_groups']:
            target_group_name = target_group['target_group_name']
            for backend in target_group['backends']:
                cls.deregister_backend(name, target_group_name, backend['host'])
            cls.deregister_target_group(name, target_group_name)
        service.delete()
        return True

    @classmethod
    def describe_service(cls, service_name):
        try:
            service = ServiceModel.get(service_name)
        except ServiceModel.DoesNotExist:
            raise Service.DoesNotExist(service_name)
        target_groups = TargetGroupModel.query(service_name)
        target_groups = sorted([tg.as_dict() for tg in target_groups], key=itemgetter('target_group_name'))
        for target_group in target_groups:
            target_group_name = target_group.get('target_group_name')
            target_group["backends"] = sorted(
                list(
                    map(lambda backend: backend.as_dict(),
                        BackendModel.scan(service_name__eq=service_name,
                                          target_group_name__eq=target_group_name))
                ),
                key=itemgetter('host'))

        data = service.as_dict()
        data['target_groups'] = target_groups
        return data

    @classmethod
    def query_resolvers(cls):
        # Resolvers
        resolvers = []
        for resolver in ResolverModel.scan():
            resolvers.append(resolver.as_dict())
        return resolvers

    @classmethod
    def query_services(cls):
        data = {s.name: s.as_dict() for s in ServiceModel.scan()}
        for target_group in TargetGroupModel.scan():
            svc_name = target_group.service_name
            data[svc_name]['target_groups'] = data[svc_name].get('target_groups', [])
            data[svc_name]['target_groups'].append(target_group.as_dict())
            data[svc_name]['target_groups'] = \
                sorted(data[svc_name]['target_groups'], key=itemgetter('target_group_name'))

        for backend in BackendModel.scan():
            svc_name = backend.service_name
            position = next(index for (index, d) in
                            enumerate(data[svc_name]['target_groups']) if
                            d["target_group_name"] == backend.target_group_name)
            data[svc_name]['target_groups'][position]['backends'] = \
                data[svc_name]['target_groups'][position].get('backends', [])
            data[svc_name]["target_groups"][position]['backends'].append(backend.as_dict())
            data[svc_name]["target_groups"][position]['backends'] = \
                sorted(data[svc_name]['target_groups'][position]['backends'], key=itemgetter('host'))
        return list(data.values())

    @classmethod
    def register_target_group(cls, target_group_definition):
        valid, errors = cls.validate_target_group(target_group_definition)
        if not valid:
            raise cls.NotValid(errors)
        service_name = target_group_definition.get('service_name')
        try:
            ServiceModel.get(service_name)
        except ServiceModel.DoesNotExist:
            raise Service.DoesNotExist(service_name)
        target_group = TargetGroupModel(
            **target_group_definition
        )
        target_group.save()
        return target_group.as_dict()

    @classmethod
    def deregister_target_group(cls, service_name, target_group_name):
        try:
            target_group = TargetGroupModel.get(service_name, target_group_name)
        except TargetGroupModel.DoesNotExist:
            raise Service.DoesNotExist("{} - {}".format(service_name, target_group_name))
        target_group.delete()
        return True

    @classmethod
    def register_backend(cls, backend_definition):
        valid, errors = cls.validate_backend(backend_definition)
        if not valid:
            raise cls.NotValid(errors)
        service_name = backend_definition.get('service_name')
        target_group_name = backend_definition.get('target_group_name')
        try:
            ServiceModel.get(service_name)
        except ServiceModel.DoesNotExist:
            raise Service.DoesNotExist(service_name)
        try:
            TargetGroupModel.get(service_name, target_group_name)
        except TargetGroupModel.DoesNotExist:
            raise Service.DoesNotExist(target_group_name)

        backend = BackendModel(
            **backend_definition
        )
        backend.save()
        return backend.as_dict()

    @classmethod
    def deregister_backend(cls, service_name, target_group_name, host):
        try:
            backend = BackendModel.get(service_name, host)
        except BackendModel.DoesNotExist:
            raise Service.DoesNotExist("{} - {}".format(service_name, host))
        backend.delete()
        return True

    @staticmethod
    def validate_service(data):
        rules = {
            "name": [Required, Length(3, 25)],
            "fqdn": [Required],
            "healthcheck_path": [],
            "healthcheck_interval": [Range(1000, 60000)],
            "healthcheck_rise": [Range(0, 20)],
            "healthcheck_fall": [Range(0, 20)],
        }
        return validate(rules, data)

    @staticmethod
    def validate_target_group(data):
        rules = {
            "service_name": [Required, Length(3, 25)],
            "target_group_name": [Required],
            "weight": [Required, Range(0, 256)],
        }
        return validate(rules, data)

    @staticmethod
    def validate_backend(data):
        rules = {
            "host": [Required, ValidHostWithPort()],
            "service_name": [Required, Length(3, 25)],
            "target_group_name": [Required],
        }
        return validate(rules, data)

    @classmethod
    def register_resolver(cls, resolver_def):
        valid, errors = cls.validate_resolver(resolver_def)
        if not valid:
            raise cls.NotValid(errors)
        resolver = ResolverModel(**resolver_def)
        resolver.save()
        return resolver.as_dict()

    @staticmethod
    def validate_resolver(data):
        rules = {
            "resolver_name": [Required, Pattern('^\S*$')],
            "nameserver_address": [Required, ValidHost()]
        }
        return validate(rules, data)

    @staticmethod
    def deregister_resolver(name):
        try:
            resolver = ResolverModel.get(name)
        except ResolverModel.DoesNotExist:
            raise Service.DoesNotExist("resolver - {}".format(name))

        resolver.delete()
        return True

    @classmethod
    def describe_resolver(cls, resolver_name):
        try:
            resolver = ResolverModel.get(resolver_name)
        except ResolverModel.DoesNotExist:
            raise Service.DoesNotExist(resolver_name)

        data = resolver.as_dict()
        return data
