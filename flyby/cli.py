import click
from pytz import utc
from flyby.haproxy import Haproxy
from apscheduler.schedulers.background import BackgroundScheduler
from flyby.models import ServiceModel, BackendModel, TargetGroupModel
from flyby.service import Service
from flyby.server import app
from sys import exit
try:
    from flyby.gunicorn import StandaloneApplication
except ImportError:
    logger.info("Unable to import StandaloneApplication from gunicorn, Windows is not supported")
    exit(0)
import threading
import logging
import logging.config
import time
import yaml


logger = logging.getLogger(__name__)
metrics = logging.getLogger('metrics')

@click.group()
def cli():
    pass


def update(fqdn, dynamo_region, dynamo_host, table_root):
    start_time = time.time()
    models = [BackendModel, ServiceModel, TargetGroupModel]
    for model in models:
        model.Meta.table_name = "{0}-{1}".format(table_root, model.Meta.table_name)
        model.Meta.region = dynamo_region
        if dynamo_host:
            model.Meta.host = dynamo_host
        if not model.exists():
            logger.info("Creating {} table".format(model.Meta.table_name))
            model.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
    services = Service.query_services()
    Haproxy().update(fqdn=fqdn, services=services)
    metrics.info('background-refresh.duration {}'.format(time.time() - start_time))
    metrics.info('active-thread-count {}'.format(threading.active_count()))


@cli.command()
@click.option('--fqdn', '-f',
              envvar="FB_FQDN",
              default="flyby.example.com",
              help="Flyby's fully qualified domain name. ie flyby.example.com")
@click.option('--dynamo-region', '-r',
              default='eu-west-1',
              help="The AWS region of the DynamoDB tables Flyby stores config in")
@click.option('--dynamo-host', '-d',
              default=None,
              help="The host to use for DynamoDB connections, used for local testing or proxying")
@click.option('--table-root', '-t',
              default='flyby',
              help="The root name of the DynamoDB table flyby stores config in, all tables will start with this")
@click.option('--log-config', envvar='FLYBY_LOG_CONFIG', help='python yaml config file', default=None)
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
        StandaloneApplication(app).run()
