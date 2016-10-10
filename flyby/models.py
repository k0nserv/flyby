from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from pynamodb.attributes import NumberAttribute
from pynamodb.attributes import BooleanAttribute
from pynamodb.attributes import UTCDateTimeAttribute
from configobj import ConfigObj, flatten_errors
from validate import Validator


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


class DynamoCapacityManagement:

    @staticmethod
    def _return_table_config(table_name):
        """
        Return the table configuration from a config file
        :param table_name:
        :return:
        """
        config = ConfigObj(infile='config.ini', configspec='flyby/configspec.ini', stringify=True)
        config.validate(Validator(), preserve_errors=True)
        for section in config.sections:
            for k, v in config[section][table_name].items():
                yield(k, v)

    def return_capacity(self, default_table_name):
        """
        return the read/write capacity requirements
        :param default_table_name:
        :return:
        """
        capacity_values = {}
        for k, v in self._return_table_config(default_table_name):
            if k in ['ReadCapacityUnits', 'WriteCapacityUnits']:
                capacity_values.update({k: int(v)})
        return capacity_values

    def capacity_check(self, default_table_name, table_name, conn):
        """
        return the read and write capacity of the given table
        :param table_name:
        :param conn: pynamodb connection object
        :param default_table_name: name of the table, as specified in the model (no table root)
        :return: dict
        """
        config_results = self.return_capacity(default_table_name)
        pynamo_results = {}
        dynamo_table = conn.describe_table(table_name=table_name)
        for k, v in dynamo_table['ProvisionedThroughput'].items():
            if k in ['ReadCapacityUnits', 'WriteCapacityUnits']:
                pynamo_results.update({k.lower():int(v)})
        return {
            'result': pynamo_results == config_results,
            'decreases': dynamo_table['ProvisionedThroughput']['NumberOfDecreasesToday'],
            'read': config_results['ReadCapacityUnits'],
            'write': config_results['WriteCapacityUnits']
        }
