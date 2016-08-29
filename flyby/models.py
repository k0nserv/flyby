from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from pynamodb.attributes import NumberAttribute


class ServiceModel(Model):
    """
    Service Model
    """
    class Meta:
        table_name = "flyby-service"
    name = UnicodeAttribute(hash_key=True)
    fqdn = UnicodeAttribute()
    healthcheck_path = UnicodeAttribute(default='/')
    healthcheck_interval = NumberAttribute(default=5000)
    healthcheck_rise = NumberAttribute(default=10)
    healthcheck_fall = NumberAttribute(default=3)

    def as_dict(self):
        return {
            'name': self.name,
            'fqdn': self.fqdn,
            'healthcheck_interval': self.healthcheck_interval,
            'healthcheck_path': self.healthcheck_path,
            'healthcheck_rise': self.healthcheck_rise,
            'healthcheck_fall': self.healthcheck_fall,
        }

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class ServiceBackendModel(Model):
    """
    Service Backend Model
    """
    class Meta:
        table_name = "flyby-service-backend"

    service_name = UnicodeAttribute(hash_key=True)
    host = UnicodeAttribute(range_key=True)

    def as_dict(self):
        return {
            'host': self.host,
        }

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
