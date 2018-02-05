__author__ = 'mpetyx (Michael Petychakis)'
__version__ = "1.0.0"
__maintainer__ = "Michael Petychakis"
__email__ = "michael@orfium.com"
__status__ = "Production"


from celery import shared_task

@shared_task(ignore_result=True)
def async_client_create_event(api_client, event_model):
    api_client.create_event(event_model)