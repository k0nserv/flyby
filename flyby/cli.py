import click
from pytz import utc
from flyby.haproxy import Haproxy
from apscheduler.schedulers.background import BackgroundScheduler
from flyby.models import ServiceModel, BackendModel, TargetGroupModel, ResolverModel
from flyby.service import Service
from flyby.server import app
from sys import exit
import threading
import logging
import logging.config
import time
import yaml
from waitress import serve
from pynamodb.connection import Connection
import configparser


logger = logging.getLogger(__name__)
metrics = logging.getLogger('metrics')


@click.group()
def cli():
    pass


def update(fqdn, dynamo_region, dynamo_host, table_root):
    start_time = time.time()
    models = [BackendModel, ServiceModel, TargetGroupModel, ResolverModel]
    for model in models:
        if not model.Meta.table_name.startswith(table_root):
            model.Meta.table_name = "{0}-{1}".format(table_root, model.Meta.table_name)
        default_table_name = model.Meta.table_name.replace('{}-'.format(table_root), "")
        model.Meta.region = dynamo_region
        if dynamo_host:
            model.Meta.host = dynamo_host
            conn = Connection(host=dynamo_host)
        else:
            conn = Connection(region=dynamo_region)
        if model.exists():
            table_capacity = capacity_check(default_table_name, model.Meta.table_name, conn)
            if not table_capacity['result'] and table_capacity['decreases'] < 4:
                conn.update_table(
                    table_name=model.Meta.table_name, read_capacity_units=table_capacity['read'],
                    write_capacity_units=table_capacity['write']
                )
                logger.info("Updating {} table read/write capacity".format(model.Meta.table_name))
            elif not table_capacity['result'] and 4 >= 4:
                logger.error("Unable to decrease capacity on {} table".format(model.Meta.table_name))
        if not model.exists():
            logger.info("Creating {} table".format(model.Meta.table_name))
            read_capacity_units = _return_capacity(default_table_name)['readcapacityunits']
            write_capacity_units = _return_capacity(default_table_name)['writecapacityunits']
            model.create_table(read_capacity_units=read_capacity_units,
                               write_capacity_units=write_capacity_units,
                               wait=True
                               )
    resolvers = Service.query_resolvers()
    services = Service.query_services()
    Haproxy().update(fqdn=fqdn, resolvers=resolvers, services=services)
    metrics.info('background-refresh.duration {}'.format(time.time() - start_time))
    metrics.info('active-thread-count {}'.format(threading.active_count()))


@cli.command()
@click.option('--fqdn', '-f',
              envvar="FLYBY_FQDN",
              default="flyby.example.com",
              help="Flyby's fully qualified domain name. ie flyby.example.com")
@click.option('--dynamo-region', '-r',
              envvar="FLYBY_DYNAMO_REGION",
              default='eu-west-1',
              help="The AWS region of the DynamoDB tables Flyby stores config in")
@click.option('--dynamo-host', '-d',
              envvar="FLYBY_DYNAMO_HOST",
              default=None,
              help="The host to use for DynamoDB connections, used for local testing or proxying")
@click.option('--table-root', '-t',
              envvar="FLYBY_TABLE_ROOT",
              default='flyby',
              help="The root name of the DynamoDB table flyby stores config in, all tables will start with this")
@click.option('--log-config',
              envvar='FLYBY_LOG_CONFIG',
              default=None,
              help='python yaml config file')
@click.option('-v', '--verbosity',
              help='Logging verbosity',
              type=click.Choice(
                  ['NOTSET', 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']),
              default='INFO')
@click.option('-e', '--environment',
              envvar='FLYBY_ENVIRONMENT',
              help='development or production',
              type=click.Choice(
                  ['development', 'production']),
              default='development')
def start(fqdn, dynamo_region, dynamo_host, table_root, log_config, verbosity, environment):
    """
    Starts an APScheduler job to periodically reload HAProxy config as well as run the API to register/deregister
    new services, target groups and backends.
    :param fqdn: The fully qualified domain name of Flyby - requests coming here will go to the API endpoints
    :param dynamo_region: The AWS region of the DynamoDB tables Flyby stores and reads config in
    :param dynamo_host: The hostname and port to use for DynamoDB connections. Useful for local testing with
    moto or DynamoDB Local.
    :param table_root: The root that will be used for table names in DynamboDB. This will be prefixed to all tables
    created.
    :param log_config: Location of python yaml config file.
    :param verbosity: Logging verbosity, defaults to INFO.
    :return:
    """
    logging.getLogger().setLevel(level=getattr(logging, verbosity))
    if log_config:
        with open(log_config, 'r') as conf:
            logging.config.dictConfig(yaml.load(conf))
    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(update, 'interval', seconds=10, args=(fqdn, dynamo_region, dynamo_host, table_root))
    scheduler.start()
    if environment == "development":
        app.run(host='0.0.0.0')
    else:
        serve(app, listen='*:5000')


def _return_table_config(table_name):
    """
    Return the table configuration from a config file
    :param table_name:
    :return:
    """
    config = configparser.ConfigParser()
    config.read('flyby/config/config.ini')
    for section in config.sections():
        for k, v in dict((config.items(section))).items():
            if section == table_name:
                yield(k, v)


def _return_capacity(default_table_name):
    """
    return the read/write capacity requirements
    :param default_table_name:
    :return:
    """
    capacity_values = {}
    for k,v in _return_table_config(default_table_name):
        if k in ['ReadCapacityUnits'.lower(), 'WriteCapacityUnits'.lower()]:
            capacity_values.update({k: int(v)})
    return capacity_values


def capacity_check(default_table_name, table_name, conn):
    """
    return the read and write capacity of the given table
    :param table_name:
    :param conn: pynamodb connection object
    :param default_table_name: name of the table, as specified in the model (no table root)
    :return: dict
    """
    config_results = _return_capacity(default_table_name)
    pynamo_results = {}
    dynamo_table = conn.describe_table(table_name=table_name)
    for k,v in dynamo_table['ProvisionedThroughput'].items():
        if k in ['ReadCapacityUnits', 'WriteCapacityUnits']:
            pynamo_results.update({k.lower():int(v)})
    return {
        'result': pynamo_results == config_results,
        'decreases': dynamo_table['ProvisionedThroughput']['NumberOfDecreasesToday'],
        'read': config_results['readcapacityunits'],
        'write': config_results['writecapacityunits']
    }
