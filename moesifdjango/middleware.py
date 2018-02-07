from __future__ import print_function

import requests
import threading
import copy
import json
import base64
import re
import django

from django.conf import settings
from django.utils import timezone
from moesifapi.moesif_api_client import *
from moesifapi.api_helper import *
from moesifapi.exceptions.api_exception import *
from moesifapi.models import *
from django.http import HttpRequest, HttpResponse
from .http_response_catcher import HttpResponseCatcher
from .masks import *
import logging

# Logger Config
logging.basicConfig()
logger = logging.getLogger('logger')

CELERY = False
if settings.MOESIF_MIDDLEWARE.get('USE_CELERY', False):
    try:
        import celery
        from .tasks import async_client_create_event
        CELERY = True
    except:
        logger.warning("USE_CELERY flag was set to TRUE, but celery package not found.")
        CELERY = False

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def moesif_middleware(*args):
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
    regex_http_ = re.compile(r'^HTTP_.+$')
    regex_content_type = re.compile(r'^CONTENT_TYPE$')
    regex_content_length = re.compile(r'^CONTENT_LENGTH$')

    def middleware(request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        req_time = timezone.now()
        raw_request_body = copy.copy(request.body)

        if DEBUG:
            print("raw body before getting response" + raw_request_body)

        if (len(args) < 1):
            print("""
             Looks like you're using Django version """ + django.get_version() + """ .
             You need to use the older version of Moesif middleware.
             See https://www.moesif.com/docs/server-integration/django/#changes-in-django-110
             """)
            return None

        response = args[0](request)
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
        regex_http_start = re.compile('^HTTP_')
        try:
            for header in request.META:
                if regex_http_.match(header) or regex_content_type.match(header) or regex_content_length.match(header):
                    normalized_header = regex_http_start.sub('', header)
                    normalized_header = normalized_header.replace('_', '-')
                    req_headers[normalized_header] = request.META[header]
            req_headers = mask_headers(req_headers, middleware_settings.get('REQUEST_HEADER_MASKS'))
        except Exception as inst:
            if DEBUG:
                print("error encountered while copying request header")
                print(inst)
            req_headers = {}

        if DEBUG:
            print("about to print what is in meta %d " % len(request.META))
            for x in request.META:
                print(x, ':', request.META[x])
            print("about to print headers %d " % len(req_headers))
            for x in req_headers:
                print(x, ':', req_headers[x])

        def flatten_to_string(value):
            if type(value) == str:
                return value
            if value is None:
                return ''
            return APIHelper.json_serialize(value)

        req_headers = {k: flatten_to_string(v) for k, v in req_headers.items()}

        req_body = None
        req_body_transfer_encoding = None
        try:
            # print("about to serialize request body" + request.body)
            if DEBUG:
                print("about to process request body" + raw_request_body)
            if raw_request_body:
                req_body = json.loads(raw_request_body)
                req_body = mask_body(req_body, middleware_settings.get('REQUEST_BODY_MASKS'))
        except:
            if raw_request_body:
                req_body = base64.standard_b64encode(raw_request_body)
                req_body_transfer_encoding = 'base64'

        ip_address = get_client_ip(request)
        uri = request.scheme + "://" + request.get_host() + request.get_full_path()

        def mapper(key):
            return copy.deepcopy(response[key])

        # a little hacky, using _headers, which is intended as a private variable.
        rsp_headers = {k: mapper(k) for k, v in response._headers.items()}

        rsp_headers = mask_headers(rsp_headers, middleware_settings.get('RESPONSE_HEADER_MASKS'))

        rsp_body = None
        rsp_body_transfer_encoding = None
        if DEBUG:
            print("about to process response")
            print(response.content)
        if response.content:
            try:
                rsp_body = json.loads(response.content)
                if DEBUG:
                    print("json parsed succesfully")
                rsp_body = mask_body(rsp_body, middleware_settings.get('RESPONSE_BODY_MASKS'))

            except:
                if DEBUG:
                    print("could not json parse, so base64 encode")
                rsp_body = base64.standard_b64encode(response.content)
                rsp_body_transfer_encoding = 'base64'
                if DEBUG:
                    print("base64 encoded body: " + rsp_body)

        rsp_time = timezone.now()

        event_req = EventRequestModel(time=req_time.isoformat(),
                                      uri=uri,
                                      verb=request.method,
                                      api_version=api_version,
                                      ip_address=ip_address,
                                      headers=req_headers,
                                      body=req_body,
                                      transfer_encoding=req_body_transfer_encoding)

        event_rsp = EventResponseModel(time=rsp_time.isoformat(),
                                       status=response.status_code,
                                       headers=rsp_headers,
                                       body=rsp_body,
                                       transfer_encoding=rsp_body_transfer_encoding)

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

        metadata = None
        try:
            get_metadata = middleware_settings.get('GET_METADATA', None)
            if get_metadata is not None:
                metadata = get_metadata(request, response)
        except:
            if DEBUG:
                print("can not execute get_metadata function, please check moesif settings.")

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
                                 session_token=session_token,
                                 metadata=metadata)

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
            try:
                if not CELERY:
                    api_client.create_event(event_model)
                else:
                    async_client_create_event.delay(event_model.to_dictionary())
                if DEBUG:
                    print("sent done")
            except APIException as inst:
                if 401 <= inst.response_code <= 403:
                    print("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                if DEBUG:
                    print("Error sending event to Moesif, with status code:")
                    print(inst.response_code)

        if CELERY:
            sending_event()
        else:
            # send the event to moesif via background so not blocking
            sending_background_thread = threading.Thread(target=sending_event)
            sending_background_thread.start()

        return response

    return middleware
