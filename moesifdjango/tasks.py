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

middleware_settings = settings.MOESIF_MIDDLEWARE
client = MoesifAPIClient(middleware_settings.get('APPLICATION_ID'))

api_client = client.api
response_catcher = HttpResponseCatcher()
api_client.http_call_back = response_catcher

@shared_task(ignore_result=True)
def async_client_create_event( event_model):
    api_client.create_event(EventModel().from_dictionary(event_model))
