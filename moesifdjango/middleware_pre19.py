from __future__ import print_function

import requests
import threading
import copy
import json
import base64
import re
import random

from django.conf import settings
from django.utils import timezone
from moesifapi.moesif_api_client import *
from moesifapi.api_helper import *
from moesifapi.exceptions.api_exception import *
from moesifapi.models import *
from django.http import HttpRequest, HttpResponse
from .http_response_catcher import HttpResponseCatcher
from .masks import *
from .client_ip import *
from update_users import *
from io import BytesIO
from moesifpythonrequest.start_capture.start_capture import StartCapture
from datetime import datetime, timedelta
import uuid

class MoesifMiddlewarePre19(object):

    # One-time configuration and initialization.
    def __init__(self):
        self.middleware_settings = settings.MOESIF_MIDDLEWARE
        self.DEBUG = self.middleware_settings.get('LOCAL_DEBUG', False)
        self.client = MoesifAPIClient(self.middleware_settings.get('APPLICATION_ID'))
        # below comment for setting moesif base_uri to a test server.
        if self.middleware_settings.get('LOCAL_DEBUG', False):
            Configuration.BASE_URI = self.middleware_settings.get('LOCAL_MOESIF_BASEURL', 'https://api.moesif.net')
        if settings.MOESIF_MIDDLEWARE.get('CAPTURE_OUTGOING_REQUESTS', False):
            try:
                if self.DEBUG:
                    print('Start capturing outgoing requests')
                # Start capturing outgoing requests
                StartCapture().start_capture_outgoing(settings.MOESIF_MIDDLEWARE)
            except:
                print('Error while starting to capture the outgoing events')
        self.api_version = self.middleware_settings.get('API_VERSION')
        self.api_client = self.client.api
        response_catcher = HttpResponseCatcher()
        self.api_client.http_call_back = response_catcher
        self.regex_http_          = re.compile(r'^HTTP_.+$')
        self.regex_content_type   = re.compile(r'^CONTENT_TYPE$')
        self.regex_content_length = re.compile(r'^CONTENT_LENGTH$')
        self.config_dict = {}
        self.sampling_percentage = self.get_config(None)
        self.transaction_id = None

    def get_config(self,cached_config_etag):
        """Get Config"""
        sample_rate = 100
        try:
            config_api_response = self.api_client.get_app_config()
            response_config_etag = config_api_response.headers.get("X-Moesif-Config-ETag")
            if cached_config_etag:
                if cached_config_etag in self.config_dict: del self.config_dict[cached_config_etag]
            self.config_dict[response_config_etag] = json.loads(config_api_response.raw_body)
            app_config = self.config_dict.get(response_config_etag)
            if app_config is not None:
                sample_rate = app_config.get('sample_rate', 100)
            self.last_updated_time = datetime.utcnow()
        except:
            self.last_updated_time = datetime.utcnow()
        return sample_rate

    def process_request(self, request):
        request.moesif_req_time = timezone.now()
        if request.META.get('CONTENT_TYPE', None) and not request.META.get('CONTENT_TYPE').startswith('multipart/form-data'):
            request._mo_body = request.body
            request._stream = BytesIO(request.body)
            request._read_started = False
        else:
            request._mo_body = None

    def process_response(self, request, response):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        req_time = request.moesif_req_time

        if self.DEBUG:
            print("raw body before getting response")

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

        # Add transaction id to request headers
        capture_transaction_id = self.middleware_settings.get('DISABLE_TRANSACTION_ID', False)
        if not capture_transaction_id:
            req_trans_id = req_headers.get("X-MOESIF-TRANSACTION-ID", None)
            if req_trans_id:
                self.transaction_id = req_trans_id
                if not self.transaction_id:
                    self.transaction_id = str(uuid.uuid4())
            else:
                self.transaction_id = str(uuid.uuid4())
            # Add transaction id to the request header
            req_headers["X-MOESIF-TRANSACTION-ID"] = self.transaction_id

        req_body = None
        req_body_transfer_encoding = None
        try:
            # print("about to serialize request body" + request.body)
            if self.DEBUG:
                print("about to process request body")
            if request._mo_body:
                req_body = json.loads(request._mo_body)
        except:
            if request._mo_body:
                req_body = base64.standard_b64encode(request._mo_body)
                req_body_transfer_encoding = 'base64'


        ip_address = get_client_ip(request)
        uri = request.scheme + "://" + request.get_host() + request.get_full_path()

        def mapper(key):
            return copy.deepcopy(response[key])

        # Add transaction id to request headers
        if self.transaction_id:
            response._headers["x-moesif-transaction-id"] = ("X-Moesif-Transaction-Id", self.transaction_id)

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
            identify_user = self.middleware_settings.get('IDENTIFY_USER', None)
            if identify_user is not None:
                username = identify_user(request, response)
        except:
            if self.DEBUG:
                print("can not execute identify_user function, please check moesif settings.")

        metadata = None
        try:
            get_metadata = self.middleware_settings.get('GET_METADATA', None)
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
                event_api_response = self.api_client.create_event(event_model)
                cached_config_etag = next(iter(self.config_dict))
                event_response_config_etag = event_api_response.get("X-Moesif-Config-ETag")

                if event_response_config_etag is not None \
                        and cached_config_etag != event_response_config_etag \
                        and datetime.utcnow() > self.last_updated_time + timedelta(minutes=5):
                    self.sampling_percentage = self.get_config(cached_config_etag)
                if self.DEBUG:
                    print("sent done")
            except APIException as inst:
                if 401 <= inst.response_code <= 403:
                    print("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                if self.DEBUG:
                    print("Error sending event to Moesif, with status code:")
                    print(inst.response_code)

        random_percentage = random.random() * 100

        if self.sampling_percentage >= random_percentage:
            # send the event to moesif via background so not blocking
            sending_background_thread = threading.Thread(target=sending_event)
            sending_background_thread.start()

        return response

    def update_user(self, user_profile):
        update_user(user_profile, self.api_client, self.DEBUG)

    def update_users_batch(self, user_profiles):
        update_users_batch(user_profiles, self.api_client, self.DEBUG)