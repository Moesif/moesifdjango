from __future__ import print_function

import requests
import threading

from django.conf import settings
from django.utils import timezone
from moesifapi.moesif_api_client import *
from moesifapi.models import *
from django.http import HttpRequest, HttpResponse
from .http_response_catcher import HttpResponseCatcher

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def moesif_middleware(get_response):
    # One-time configuration and initialization.
    middleware_settings = settings.MOESIF_MIDDLEWARE
    client = MoesifAPIClient(middleware_settings.get('APPLICATION_ID'))
    # below comment for setting moesif base_uri to a test server.
    # Configuration.BASE_URI = 'http://192.168.0.5:8000/_moesif/api'
    api_version = middleware_settings.get('API_VERSION')
    api_client = client.api
    response_catcher = HttpResponseCatcher()
    api_client.http_call_back = response_catcher

    def middleware(request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        req_time = timezone.now()
        req_body = None
        if request.body:
            print("about to serialize body" + request.body)
            req_body = APIHelper.json_deserialize(request.body)
        ip_address = get_client_ip(request)

        response = get_response(request)
        # Code to be executed for each request/response after
        # the view is called.


        uri = request.scheme + "://" + request.get_host() + request.get_full_path()


        def mapper(key):
            return response[key]
        # a little hacky, using _headers, which is intended as a private variable.
        rsp_headers = {k: mapper(k) for k, v in response._headers.items()};

        print("response headers:")
        print(rsp_headers);

        rsp_body = APIHelper.json_deserialize(response.content);
        if not response.content:
            rsp_body = {}

        rsp_time = timezone.now()

        event_req = EventRequestModel(time=req_time.isoformat(),
                                      uri=uri,
                                      verb=request.method,
                                      api_version=api_version,
                                      ip_address=ip_address,
                                      headers=request.META,
                                      body=req_body)

        event_rsp = EventResponseModel(time=req_time.isoformat(),
                                       status=response.status_code,
                                       headers=rsp_headers,
                                       body=rsp_body)

        event_model = EventModel(request=event_req,
                                 response=event_rsp,
                                 user_id="my_user_id",
                                 session_token="23jdf0owekfmcn4u3qypxg09w4d8ayrcdx8nu2ng]s98y18cx98q3yhwmnhcfx43f")

        def sending_event():
            print("sending event to moesif")
            api_client.create_event(event_model)
            print("sending finished")

        # send the event to moesif via background so not blocking
        sending_background_thread = threading.Thread(target=sending_event)
        sending_background_thread.start()

        return response
    return middleware
