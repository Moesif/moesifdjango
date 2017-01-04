from __future__ import print_function

import requests
import threading
import copy
import json

from django.conf import settings
from django.utils import timezone
from moesifapi.moesif_api_client import *
from moesifapi.api_helper import *
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
    DEBUG = middleware_settings.get('LOCAL_DEBUG', False)
    client = MoesifAPIClient(middleware_settings.get('APPLICATION_ID'))
    # below comment for setting moesif base_uri to a test server.
    if middleware_settings.get('LOCAL_DEBUG', False):
        Configuration.BASE_URI = middleware_settings.get('LOCAL_MOESIF_BASEURL', 'https://api.moesif.net')
    api_version = middleware_settings.get('API_VERSION')
    api_client = client.api
    response_catcher = HttpResponseCatcher()
    api_client.http_call_back = response_catcher


    def middleware(request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        req_time = timezone.now()
        raw_request_body = copy.copy(request.body)

        if DEBUG:
            print("raw body before getting response" + raw_request_body)

        response = get_response(request)
        # Code to be executed for each request/response after
        # the view is called.

        try:
            skip_event = middleware_settings.get('SKIP', None)
            if skip_event is not None:
                if skip_event(request, response):
                    return response
        except:
            if DEBUG:
                print("Having difficulty executing skip_event function. Please check moesif settings.")

        req_headers = {}
        try:
            req_headers = copy.deepcopy(request.META)
            req_headers = mask_headers(req_headers, middleware_settings.get('REQUEST_HEADER_MASKS'))
        except:
            req_headers = {}

        def flatten_to_string(value):
            if type(value) == str:
                return value
            if value is None:
                return ''
            return APIHelper.json_serialize(value)

        req_headers = {k: flatten_to_string(v) for k, v in req_headers.items()}

        req_body = None
        try:
            # print("about to serialize request body" + request.body)
            if DEBUG:
                print("about process request body" + raw_request_body)
            if raw_request_body:
                req_body = json.loads(raw_request_body)
                req_body = mask_body(req_body, middleware_settings.get('REQUEST_BODY_MASKS'))
        except:
            req_body = {
                "moesif_error": {
                    "code": "json_parse_error",
                    "src": "moesifdjango",
                    "msg": ["Body is not a JSON Object or JSON Array"],
                    "args": [str(raw_request_body)],
                }
            }
            #"code": "can not serialize request body=" + str(raw_request_body)

        ip_address = get_client_ip(request)
        uri = request.scheme + "://" + request.get_host() + request.get_full_path()

        def mapper(key):
            return copy.deepcopy(response[key])

        # a little hacky, using _headers, which is intended as a private variable.
        rsp_headers = {k: mapper(k) for k, v in response._headers.items()}

        rsp_headers = mask_headers(rsp_headers, middleware_settings.get('RESPONSE_HEADER_MASKS'))

        rsp_body = {}
        try:
            rsp_body = APIHelper.json_deserialize(response.content)
            rsp_body = mask_body(rsp_body, middleware_settings.get('RESPONSE_BODY_MASKS'))
        except:
            rsp_body = {
                "moesif_error": {
                    "code": "json_parse_error",
                    "src": "moesifdjango",
                    "msg": ["Body is not a JSON Object or JSON Array"],
                    "args": [str(response.content)],
                }
            }
            #rsp_body = {"message": "can not serialize response body=" + str(response.content)}

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

        try:
            identify_user = middleware_settings.get('IDENTIFY_USER', None)
            if identify_user is not None:
                username = identify_user(request, response)
        except:
            if DEBUG:
                print("can not execute identify_user function, please check moesif settings.")


        session_token = None
        try:
            session_token = request.session.session_key
        except:
            session_token = None

        try:
            get_session_token = middleware_settings.get('GET_SESSION_TOKEN', None)
            if get_session_token is not None:
                session_token = get_session_token(request, response)
        except:
            if DEBUG:
                print("Can not execute get_session_token function. Please check moesif settings.")


        event_model = EventModel(request=event_req,
                                 response=event_rsp,
                                 user_id=username,
                                 session_token=session_token)

        try:
            mask_event_model = middleware_settings.get('MASK_EVENT_MODEL', None)
            if mask_event_model is not None:
                event_model = mask_event_model(event_model)
        except:
            if DEBUG:
                print("Can not execute MASK_EVENT_MODEL function. Please check moesif settings.")

        def sending_event():
            if DEBUG:
                print("sending event to moesif")
            api_client.create_event(event_model)
            if DEBUG:
                print("sending finished")

        # send the event to moesif via background so not blocking
        sending_background_thread = threading.Thread(target=sending_event)
        sending_background_thread.start()

        return response


    return middleware
