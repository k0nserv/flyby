import click
from pytz import utc
from flyby.haproxy import Haproxy
from apscheduler.schedulers.background import BackgroundScheduler
from flyby.models import ServiceModel, BackendModel, TargetGroupModel, ResolverModel, DynamoCapacityManagement
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


logger = logging.getLogger(__name__)
metrics = logging.getLogger('metrics')


@click.group()
def cli():
    pass


def update(fqdn, dynamo_region, dynamo_host, table_root):
    dynamo_manager = DynamoCapacityManagement()
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
            table_capacity = dynamo_manager.capacity_check(default_table_name, model.Meta.table_name, conn)
            if not table_capacity['result'] and table_capacity['decreases'] < 4:
                conn.update_table(
                    table_name=model.Meta.table_name, read_capacity_units=table_capacity['read'],
                    write_capacity_units=table_capacity['write']
                )
                logger.info("Updating {} table read/write capacity".format(model.Meta.table_name))
            elif not table_capacity['result'] and table_capacity['write'] >= 4:
                logger.error("Unable to decrease capacity on {} table".format(model.Meta.table_name))
        if not model.exists():
            logger.info("Creating {} table".format(model.Meta.table_name))
            read_capacity_units = dynamo_manager.return_capacity(default_table_name)['ReadCapacityUnits']
            write_capacity_units = dynamo_manager.return_capacity(default_table_name)['WriteCapacityUnits']
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
