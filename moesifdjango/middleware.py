from __future__ import print_function

import requests
import threading

from django.conf import settings
from django.utils import timezone
from moesifapi.moesif_api_client import *
from moesifapi.models import *
from django.http import HttpRequest, HttpResponse
from .http_response_catcher import HttpResponseCatcher
from .masks import *

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
    Configuration.BASE_URI = 'http://192.168.0.5:8000/_moesif/api'
    api_version = middleware_settings.get('API_VERSION')
    api_client = client.api
    response_catcher = HttpResponseCatcher()
    api_client.http_call_back = response_catcher

    def middleware(request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        req_time = timezone.now()

        response = get_response(request)
        # Code to be executed for each request/response after
        # the view is called.


        req_headers = {}
        if request.META is not None:
            req_headers = request.META.copy()
            req_headers = mask_headers(req_headers, middleware_settings.get('REQUEST_HEADER_MASKS'))

        req_body = None
        if request.body is not None:
            # print("about to serialize request body" + request.body)
            req_body = APIHelper.json_deserialize(request.body)
            req_body = mask_body(req_body, middleware_settings.get('REQUEST_BODY_MASKS'))

        ip_address = get_client_ip(request)
        uri = request.scheme + "://" + request.get_host() + request.get_full_path()

        def mapper(key):
            return response[key]
        # a little hacky, using _headers, which is intended as a private variable.
        rsp_headers = {k: mapper(k) for k, v in response._headers.items()};
        rsp_headers = mask_headers(rsp_headers, middleware_settings.get('RESPONSE_HEADER_MASKS'))

        print("response headers:")
        print(rsp_headers);

        rsp_body = {}
        if response.content is not None:
            rsp_body = APIHelper.json_deserialize(response.content)
            rsp_body = mask_body(rsp_body, middleware_settings.get('RESPONSE_BODY_MASKS'))

        rsp_time = timezone.now()

        event_req = EventRequestModel(time=req_time.isoformat(),
                                      uri=uri,
                                      verb=request.method,
                                      api_version=api_version,
                                      ip_address=ip_address,
                                      headers=req_headers,
                                      body=req_body)

        event_rsp = EventResponseModel(time=req_time.isoformat(),
                                       status=response.status_code,
                                       headers=rsp_headers,
                                       body=rsp_body)

        username = None
        try:
            username = request.user.username
        except:
            username = None

        session_token = None
        try:
            session_token = request.session.session_key
        except:
            session_token = None

        event_model = EventModel(request=event_req,
                                 response=event_rsp,
                                 user_id=username,
                                 session_token=session_token)

        def sending_event():
            print("sending event to moesif")
            api_client.create_event(event_model)
            print("sending finished")

        # send the event to moesif via background so not blocking
        sending_background_thread = threading.Thread(target=sending_event)
        sending_background_thread.start()

        return response
    return middleware
