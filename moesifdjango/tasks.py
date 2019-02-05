"""
__author__ = 'mpetyx (Michael Petychakis)'
__version__ = "1.0.0"
__maintainer__ = "Michael Petychakis"
__email__ = "michael@orfium.com"
__status__ = "Production"
"""

from __future__ import absolute_import, unicode_literals
from django.conf import settings
from .http_response_catcher import HttpResponseCatcher
from celery import shared_task
from moesifapi.moesif_api_client import MoesifAPIClient
from moesifapi.models import EventModel
from .app_config import AppConfig, get_config, set_config
from datetime import datetime, timedelta

middleware_settings = settings.MOESIF_MIDDLEWARE
client = MoesifAPIClient(middleware_settings.get('APPLICATION_ID'))
BATCH_SIZE = settings.MOESIF_MIDDLEWARE.get('BATCH_SIZE', 25)
DEBUG = middleware_settings.get('LOCAL_DEBUG', False)

api_client = client.api
response_catcher = HttpResponseCatcher()
api_client.http_call_back = response_catcher

try:
    get_broker_url = settings.BROKER_URL
    if get_broker_url:
        BROKER_URL = get_broker_url
    else:
        BROKER_URL = None
except AttributeError:
    BROKER_URL = settings.MOESIF_MIDDLEWARE.get('CELERY_BROKER_URL', None)

def queue_get_all(queue_events):
    events = []
    max_events_to_retreive = BATCH_SIZE
    for num_of_events_retrieved in range(0, max_events_to_retreive):
        try:
            if num_of_events_retrieved == max_events_to_retreive:
                break
            events.append(queue_events.get_nowait())
        except:
            break
    return events

@shared_task(ignore_result=True)
def async_client_create_event():
    batch_events = []
    try:
        with Connection(BROKER_URL) as conn:
            moesif_events_queue = conn.SimpleQueue('moesif_events_queue')
            try:
                queue_size = moesif_events_queue.qsize()
                while queue_size > 0:
                    message = queue_get_all(moesif_events_queue)
                    for event in message:
                        batch_events.append(EventModel().from_dictionary(event.payload))
                        event.ack()
                    try:
                        queue_size = moesif_events_queue.qsize()
                    except ChannelError:
                        queue_size = 0
                    moesif_events_queue.close()
            except ChannelError:
                if DEBUG:
                    print("No message to read from the queue")
    except:
        if DEBUG:
            print("Error while connecting to - {0}".format(BROKER_URL))

    if batch_events:
        if DEBUG:
            print("Sending events to Moesif")
        batch_events_api_response = api_client.create_events_batch(batch_events)
        cached_config_etag = next(iter(AppConfig.config_dict))
        batch_events_response_config_etag = batch_events_api_response.get("X-Moesif-Config-ETag")
        if batch_events_response_config_etag is not None \
                and cached_config_etag != batch_events_response_config_etag \
                and datetime.utcnow() > AppConfig.last_updated_time + timedelta(minutes=5):

            AppConfig.last_updated_time, AppConfig.sampling_percentage, AppConfig.config_dict = get_config(api_client, AppConfig.config_dict,
                                                                                    cached_config_etag)
            set_config(AppConfig.last_updated_time, AppConfig.sampling_percentage, AppConfig.config_dict)
        if DEBUG:
            print("Events sent successfully")
    else:
        if DEBUG:
            print("No events to send")


CELERY = False
if settings.MOESIF_MIDDLEWARE.get('USE_CELERY', False):
    if BROKER_URL:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            import atexit
            from kombu import Connection
            from kombu.exceptions import ChannelError

            scheduler = BackgroundScheduler(daemon=True)
            scheduler.start()
            scheduler.add_job(
                func=async_client_create_event,
                trigger=IntervalTrigger(seconds=5),
                id='moesif_events_batch_job',
                name='Schedule events batch job every 5 second',
                replace_existing=True)

            # Shut down the scheduler when exiting the app
            atexit.register(lambda: scheduler.shutdown())
        except:
            if DEBUG:
                print("Error when scheduling the job")
    else:
        if DEBUG:
            print("Unable to schedule the job as the BROKER_URL is not provided")
