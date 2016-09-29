from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from pynamodb.attributes import NumberAttribute
from pynamodb.attributes import BooleanAttribute
from pynamodb.attributes import UTCDateTimeAttribute


class ServiceModel(Model):
    """
    Service Model
    """
    class Meta:
        table_name = "service"
    name = UnicodeAttribute(hash_key=True)
    fqdn = UnicodeAttribute()
    healthcheck_path = UnicodeAttribute(default='/')
    healthcheck_interval = NumberAttribute(default=5000)
    healthcheck_rise = NumberAttribute(default=10)
    healthcheck_fall = NumberAttribute(default=3)
    connection_draining = NumberAttribute(default=20)
    failover_pool_fqdn = UnicodeAttribute(default="")
    failover_pool_use_https = BooleanAttribute(default=0)
    failover_pool_ssl_allow_self_signed_certs = BooleanAttribute(default=0)
    dns_resolver = UnicodeAttribute(default="")

    def as_dict(self):
        return {
            'name': self.name,
            'fqdn': self.fqdn,
            'healthcheck_interval': self.healthcheck_interval,
            'healthcheck_path': self.healthcheck_path,
            'healthcheck_rise': self.healthcheck_rise,
            'healthcheck_fall': self.healthcheck_fall,
            'connection_draining': self.connection_draining,
            'failover_pool_fqdn': self.failover_pool_fqdn,
            'failover_pool_use_https': self.failover_pool_use_https,
            'failover_pool_ssl_allow_self_signed_certs': self.failover_pool_ssl_allow_self_signed_certs,
            'dns_resolver': self.dns_resolver,
        }

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class TargetGroupModel(Model):
    """
    Service Target Group
    """
    class Meta:
        table_name = "target-group"
    service_name = UnicodeAttribute(hash_key=True)
    target_group_name = UnicodeAttribute(range_key=True)
    weight = NumberAttribute()

    def as_dict(self):
        return {
            'weight': self.weight,
            'target_group_name': self.target_group_name,
        }

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class BackendModel(Model):
    """
    Service Backend Model
    """
    class Meta:
        table_name = "backend"
    service_name = UnicodeAttribute(hash_key=True)
    target_group_name = UnicodeAttribute()
    host = UnicodeAttribute(range_key=True)
    dns_resolver = UnicodeAttribute(default="")

    updated_at = UTCDateTimeAttribute()
    status = UnicodeAttribute(default="HEALTHY")

    def as_dict(self):
        return {
            'host': self.host,
            'status': self.status
        }

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class ResolverModel(Model):
    """
    DNS Resolver Model
    """

    class Meta:
        table_name = "resolver"

    resolver_name = UnicodeAttribute(hash_key=True)
    nameserver_address = UnicodeAttribute()
    nameserver_port = NumberAttribute(default=53)
    resolve_retries = NumberAttribute(default=10)
    timeout_retry = UnicodeAttribute(default="5s")
    hold_valid = UnicodeAttribute(default="30s")

    def as_dict(self):
        return {
            'name': self.resolver_name,
            'nameserver_address': self.nameserver_address,
            'nameserver_port': self.nameserver_port,
            'resolve_retries': self.resolve_retries,
            'timeout_retry': self.timeout_retry,
            'hold_valid': self.hold_valid
        }

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
