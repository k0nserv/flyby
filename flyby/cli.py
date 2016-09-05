import click
from pytz import utc
from flyby.haproxy import Haproxy
from apscheduler.schedulers.background import BackgroundScheduler
from flyby.models import ServiceModel, BackendModel, TargetGroupModel
from flyby.service import Service
from flyby.server import app
import logging
logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


def update(fqdn, dynamo_region, dynamo_host):
    models = [BackendModel, ServiceModel, TargetGroupModel]
    for model in models:
        model.Meta.region = dynamo_region
        if dynamo_host:
            model.Meta.host = dynamo_host
        if not model.exists():
            logger.info("Creating {} table".format(model.Meta.table_name))
            model.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
    services = Service.query_services()
    Haproxy().update(fqdn=fqdn, services=services)


@cli.command()
@click.option('--fqdn',
              envvar="FB_FQDN",
              default="flyby.example.com",
              help="Flyby's fully qualified domain name. ie flyby.example.com")
@click.option('--dynamo-region',
              default='eu-west-1',
              help="The AWS region of the DynamoDB tables Flyby stores config in")
@click.option('--dynamo-host',
              default=None,
              help="The host to use for DynamoDB connections, used for local testing or proxying")
@click.option('--debug', default=False, help='Debug mode.', is_flag=True)
def start(debug, fqdn, dynamo_region, dynamo_host):
    """
    Starts an APScheduler job to periodically reload HAProxy config as well as run the API to register/deregister
    new services, target groups and backends.
    :param debug: A debug flag
    :param fqdn: The fully qualified domain name of Flyby - requests coming here will go to the API endpoints
    :param dynamo_region: The AWS region of the DynamoDB tables Flyby stores and reads config in
    :param dynamo_host: The hostname and port to use for DynamoDB connections. Useful for local testing with
    moto or DynamoDB Local.
    :return:
    """
    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(update, 'interval', seconds=10, args=(fqdn, dynamo_region, dynamo_host))
    scheduler.start()
    app.run(host='0.0.0.0')
