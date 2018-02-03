from __future__ import print_function

import requests
import threading
import copy
import json
import base64
import re

from django.conf import settings
from django.utils import timezone
from moesifapi.moesif_api_client import *
from moesifapi.api_helper import *
from moesifapi.exceptions.api_exception import *
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

class MoesifMiddlewarePre19(object):

    # One-time configuration and initialization.
    def __init__(self):
        self.middleware_settings = settings.MOESIF_MIDDLEWARE
        self.DEBUG = self.middleware_settings.get('LOCAL_DEBUG', False)
        self.client = MoesifAPIClient(self.middleware_settings.get('APPLICATION_ID'))
        # below comment for setting moesif base_uri to a test server.
        if self.middleware_settings.get('LOCAL_DEBUG', False):
            Configuration.BASE_URI = self.middleware_settings.get('LOCAL_MOESIF_BASEURL', 'https://api.moesif.net')
        self.api_version = self.middleware_settings.get('API_VERSION')
        self.api_client = self.client.api
        response_catcher = HttpResponseCatcher()
        self.api_client.http_call_back = response_catcher
        self.regex_http_          = re.compile(r'^HTTP_.+$')
        self.regex_content_type   = re.compile(r'^CONTENT_TYPE$')
        self.regex_content_length = re.compile(r'^CONTENT_LENGTH$')

    def process_request(self, request):
        request.moesif_req_time = timezone.now()
        request._body = request.body

    def process_response(self, request, response):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        req_time = request.moesif_req_time
        raw_request_body = request._body

        if self.DEBUG:
            print("raw body before getting response" + raw_request_body)

        # response = get_response(request)
        # Code to be executed for each request/response after
        # the view is called.

        try:
            skip_event = self.middleware_settings.get('SKIP', None)
            if skip_event is not None:
                if skip_event(request, response):
                    return response
        except:
            if self.DEBUG:
                print("Having difficulty executing skip_event function. Please check moesif settings.")

        req_headers = {}
        regex_http_start = re.compile('^HTTP_')
        try:
            for header in request.META:
                if self.regex_http_.match(header) or self.regex_content_type.match(header) or self.regex_content_length.match(header):
                    normalized_header = regex_http_start.sub('', header)
                    normalized_header = normalized_header.replace('_', '-')
                    req_headers[normalized_header] = request.META[header]
        except Exception as inst:
            if self.DEBUG:
                print("error encountered while copying request header")
                print(inst)
            req_headers = {}

        if self.DEBUG:
            print("about to print what is in meta %d " % len(request.META))
            for x in request.META:
                print (x, ':', request.META[x])
            print("about to print headers %d " % len(req_headers))
            for x in req_headers:
                print (x, ':', req_headers[x])


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
            if self.DEBUG:
                print("about to process request body" + raw_request_body)
            if raw_request_body:
                req_body = json.loads(raw_request_body)
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

        rsp_body = None
        rsp_body_transfer_encoding = None
        if self.DEBUG:
            print("about to process response")
            print(response.content)
        if response.content:
            try:
                rsp_body = json.loads(response.content)
                if self.DEBUG:
                    print("jason parsed succesfully")
            except:
                if self.DEBUG:
                    print("could not json parse, so base64 encode")
                rsp_body = base64.standard_b64encode(response.content)
                rsp_body_transfer_encoding = 'base64'
                if self.DEBUG:
                    print("base64 encoded body: " + rsp_body)


        rsp_time = timezone.now()

        event_req = EventRequestModel(time=req_time.isoformat(),
                                      uri=uri,
                                      verb=request.method,
                                      api_version=self.api_version,
                                      ip_address=ip_address,
                                      headers=req_headers,
                                      body=req_body,
                                      transfer_encoding=req_body_transfer_encoding)

        event_rsp = EventResponseModel(time=req_time.isoformat(),
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
            identify_user = self.middleware_settings.get('IDENTIFY_USER', None)
            if identify_user is not None:
                username = identify_user(request, response)
        except:
            if self.DEBUG:
                print("can not execute identify_user function, please check moesif settings.")

        metadata = None
        try:
            get_metadata = middleware_settings.get('GET_METADATA', None)
            if get_metadata is not None:
                metadata = get_metadata(request, response)
        except:
            if self.DEBUG:
                print("can not execute get_metadata function, please check moesif settings.")


        session_token = None
        try:
            session_token = request.session.session_key
        except:
            session_token = None

        try:
            get_session_token = self.middleware_settings.get('GET_SESSION_TOKEN', None)
            if get_session_token is not None:
                session_token = get_session_token(request, response)
        except:
            if self.DEBUG:
                print("Can not execute get_session_token function. Please check moesif settings.")


        event_model = EventModel(request=event_req,
                                 response=event_rsp,
                                 user_id=username,
                                 session_token=session_token,
                                 metadata=metadata)

        try:
            mask_event_model = self.middleware_settings.get('MASK_EVENT_MODEL', None)
            if mask_event_model is not None:
                event_model = mask_event_model(event_model)
        except:
            if self.DEBUG:
                print("Can not execute MASK_EVENT_MODEL function. Please check moesif settings.")

        def sending_event():
            if self.DEBUG:
                print("sending event to moesif")
            try:
                self.api_client.create_event(event_model)
                if self.DEBUG:
                    print("sent done")
            except APIException as inst:
                if 401 <= inst.response_code <= 403:
                    print("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                if self.DEBUG:
                    print("Error sending event to Moesif, with status code:")
                    print(inst.response_code)

        # send the event to moesif via background so not blocking
        sending_background_thread = threading.Thread(target=sending_event)
        sending_background_thread.start()

        return response
