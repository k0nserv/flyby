import click
from pytz import utc
from flyby.haproxy import Haproxy
from apscheduler.schedulers.background import BackgroundScheduler
from flyby.models import ServiceModel, ServiceBackendModel
from flyby.service import Service
from flyby.server import app
import logging
logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


def update(fqdn):
    ServiceBackendModel.Meta.region = 'eu-west-1'
    ServiceModel.Meta.region = 'eu-west-1'
    if not ServiceBackendModel.exists():
        ServiceBackendModel.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
    if not ServiceModel.exists():
        ServiceModel.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
    services = Service.query_services()
    Haproxy().update(fqdn=fqdn, services=services)


@cli.command()
@click.option('--fqdn', envvar="FB_FQDN", default="flyby.example.com", help='Flyby fully qualify domain name. ie flyby.example.com')
@click.option('--debug', default=False, help='Debug mode.', is_flag=True)
def start(debug, fqdn):
    """Simple program that greets NAME for a total of COUNT times."""
    ServiceBackendModel.Meta.region = 'eu-west-1'
    ServiceModel.Meta.region = 'eu-west-1'
    try:
        logger.info('create tables')
        ServiceModel.create_table(1, 1, True)
        ServiceBackendModel.create_table(1, 1, True)
    except:
        logger.info('could not create tables')
    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(update, 'interval', seconds=10, args=(fqdn,))
    scheduler.start()
    app.run(host='0.0.0.0')
