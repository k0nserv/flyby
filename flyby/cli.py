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


def update(fqdn):
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
@click.option('--debug', default=False, help='Debug mode.', is_flag=True)
def start(debug, fqdn, region):
    """
    Starts an APScheduler job to periodically reload HAProxy config as well as run the API to register/deregister
    new services, target groups and backends.
    :param debug: A debug flag
    :param fqdn: The fully qualified domain name of Flyby - requests coming here will go to the API endpoints
    :param region: The AWS region of the DynamoDB tables Flyby stores and reads config in
    :return:
    """
    BackendModel.Meta.region = region
    ServiceModel.Meta.region = region
    TargetGroupModel.meta.region = region
    if not BackendModel.exists():
        logger.info("Creating {} table".format("backend"))
        BackendModel.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
    if not ServiceModel.exists():
        logger.info("Creating {} table".format("service"))
        ServiceModel.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
    if not TargetGroupModel.exists():
        logger.info("Creating {} table".format("target group"))
        TargetGroupModel.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(update, 'interval', seconds=10, args=(fqdn,))
    scheduler.start()
    app.run(host='0.0.0.0')
