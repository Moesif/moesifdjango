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

# Initialization
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
    for num_of_events_retrieved in range(0, BATCH_SIZE):
        try:
            if num_of_events_retrieved == BATCH_SIZE:
                break
            events.append(queue_events.get_nowait())
        except:
            break
    return events

@shared_task(ignore_result=True)
def async_client_create_event(moesif_events_queue):
    batch_events = []
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
    except ChannelError:
        if DEBUG:
            print("No message to read from the queue")

    if batch_events:
        try:
            if DEBUG:
                print("Sending events to Moesif")
            api_client.create_events_batch(batch_events)
            if DEBUG:
                print("Events sent successfully")
        except Exception as ex:
            if DEBUG:
                print("Error sending events to Moesif")
                print(str(ex))
    else:
        if DEBUG:
            print("No events to send")

def exit_handler(moesif_events_queue, scheduler):
    try:
        # Close the queue
        moesif_events_queue.close()
        # Shut down the scheduler
        scheduler.shutdown()
    except:
        if DEBUG:
            print("Error while closing the queue or scheduler shut down")

CELERY = False
if settings.MOESIF_MIDDLEWARE.get('USE_CELERY', False):
    if BROKER_URL:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            from kombu import Connection
            from kombu.exceptions import ChannelError
            import atexit
            import logging

            scheduler = BackgroundScheduler(daemon=True)
            scheduler.start()
            try:
                conn = Connection(BROKER_URL)
                moesif_events_queue = conn.SimpleQueue('moesif_events_queue')
                scheduler.add_job(
                    func=lambda: async_client_create_event(moesif_events_queue),
                    trigger=IntervalTrigger(seconds=5),
                    id='moesif_events_batch_job',
                    name='Schedule events batch job every 5 second',
                    replace_existing=True)

                # Avoid passing logging message to the ancestor loggers
                logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
                logging.getLogger('apscheduler.executors.default').propagate = False

                # Exit handler when exiting the app
                atexit.register(lambda: exit_handler(moesif_events_queue, scheduler))
            except:
                if DEBUG:
                    print("Error while connecting to - {0}".format(BROKER_URL))
        except:
            if DEBUG:
                print("Error when scheduling the job")
    else:
        if DEBUG:
            print("Unable to schedule the job as the BROKER_URL is not provided")
