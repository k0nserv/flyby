import click
from pytz import utc
from flyby.haproxy import Haproxy
from apscheduler.schedulers.background import BackgroundScheduler
from flyby.models import DynamoTableManagement
from flyby.service import Service
from flyby.server import app
from sys import exit
import threading
import logging
import logging.config
import time
import yaml
from waitress import serve
from configobj import ConfigObj, flatten_errors
from validate import Validator


logger = logging.getLogger(__name__)
metrics = logging.getLogger('metrics')


@click.group()
def cli():
    pass


def update(fqdn):
    start_time = time.time()
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
@click.option('-c', '--server-config',
              envvar='SLG_SERVER_CONFIG',
              help='Slingshot server configuration file.')
def start(fqdn, dynamo_region, dynamo_host, table_root, log_config, verbosity, environment, server_config):
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
    dynamo_manager = DynamoTableManagement()
    config = ConfigObj(infile=server_config, configspec='flyby/configspec.ini', stringify=True)
    res = config.validate(Validator(), preserve_errors=True)
    if res is not True:
        for section, key, msg in flatten_errors(config, res):
            click.echo("{}: {} in {}".format(key, msg, section))
        raise click.ClickException('bad server config')

    # Create the DynamoDB tables if missing, update the DynamoDB read/write capacity if required
    dynamo_manager.update_capacity(dynamo_host, dynamo_region, table_root, logger, config)
    if log_config:
        with open(log_config, 'r') as conf:
            logging.config.dictConfig(yaml.load(conf))
    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(update, 'interval', seconds=10, args=(fqdn,))
    scheduler.start()
    if environment == "development":
        app.run(host='0.0.0.0')
    else:
        serve(app, listen='*:5000')
