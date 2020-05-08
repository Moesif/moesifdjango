from __future__ import print_function

import requests
import threading
import copy
import json
import base64
import re
import random
import math
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
from .update_users import *
from .update_companies import *
from io import BytesIO
from moesifpythonrequest.start_capture.start_capture import StartCapture
from datetime import datetime, timedelta
from .app_config import AppConfig
from .parse_body import ParseBody
from .update_companies import Company
from .update_users import User
from .client_ip import ClientIp
import uuid

class MoesifMiddlewarePre19(object):

    # One-time configuration and initialization.
    def __init__(self):
        self.middleware_settings = settings.MOESIF_MIDDLEWARE
        self.DEBUG = self.middleware_settings.get('LOCAL_DEBUG', False)
        self.LOG_BODY = self.middleware_settings.get('LOG_BODY', True)
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
        self.app_config = AppConfig()
        self.parse_body = ParseBody()
        self.client_ip = ClientIp()
        self.user = User()
        self.company = Company()
        self.config = self.app_config.get_config(self.api_client, self.DEBUG)
        self.sampling_percentage = 100
        self.config_etag = None
        self.last_updated_time = datetime.utcnow()
        try:
            if self.config:
                self.config_etag, self.sampling_percentage, self.last_updated_time = self.app_config.parse_configuration(
                    self.config, self.DEBUG)
        except:
            if self.DEBUG:
                print('Error while parsing application configuration on initialization')
        self.transaction_id = None

    def process_request(self, request):
        request.moesif_req_time = timezone.now()
        try:
            request._mo_body = request.body
            request._stream = BytesIO(request.body)
            request._read_started = False
        except:
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
        if self.LOG_BODY and request._mo_body:
            if isinstance(request._mo_body, str):
                req_body, req_body_transfer_encoding = self.parse_body.parse_string_body(request._mo_body,
                                                                                         self.parse_body.transform_headers(req_headers),
                                                                                         self.middleware_settings.get('REQUEST_BODY_MASKS'))
            else:
                req_body, req_body_transfer_encoding = self.parse_body.parse_bytes_body(request._mo_body,
                                                                                        self.parse_body.transform_headers(req_headers),
                                                                                        self.middleware_settings.get('REQUEST_BODY_MASKS'))


        ip_address = self.client_ip.get_client_ip(request)
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
        if self.LOG_BODY and isinstance(response, HttpResponse) and response.content:
            if isinstance(response.content, str):
                rsp_body, rsp_body_transfer_encoding = self.parse_body.parse_string_body(response.content,
                                                                                         self.parse_body.transform_headers(rsp_headers),
                                                                                         self.middleware_settings.get('RESPONSE_BODY_MASKS'))
            else:
                rsp_body, rsp_body_transfer_encoding = self.parse_body.parse_bytes_body(response.content,
                                                                                        self.parse_body.transform_headers(rsp_headers),
                                                                                        self.middleware_settings.get('RESPONSE_BODY_MASKS'))


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

        company_id = None
        try:
            identify_company = self.middleware_settings.get('IDENTIFY_COMPANY', None)
            if identify_company is not None:
                company_id = identify_company(request, response)
        except:
            if self.DEBUG:
                print("can not execute identify_company function, please check moesif settings.")

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
                                 company_id=company_id,
                                 session_token=session_token,
                                 metadata=metadata,
                                 direction="Incoming")

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
                event_response_config_etag = event_api_response.get("X-Moesif-Config-ETag")

                if event_response_config_etag is not None \
                        and self.config_etag is not None \
                        and self.config_etag != event_response_config_etag \
                        and datetime.utcnow() > self.last_updated_time + timedelta(minutes=5):
                    try:
                        self.config = self.app_config.get_config(self.api_client, self.DEBUG)
                        self.config_etag, self.sampling_percentage, self.last_updated_time = self.app_config.parse_configuration(self.config, self.DEBUG)
                    except:
                        if self.DEBUG:
                            print('Error while updating the application configuration')
                if self.DEBUG:
                    print("Event sent successfully")
            except APIException as inst:
                if 401 <= inst.response_code <= 403:
                    print("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                if self.DEBUG:
                    print("Error sending event to Moesif, with status code:")
                    print(inst.response_code)

        random_percentage = random.random() * 100

        self.sampling_percentage = self.app_config.get_sampling_percentage(self.config, username, company_id)
        if self.sampling_percentage >= random_percentage:
            event_model.weight = 1 if self.sampling_percentage == 0 else math.floor(100 / self.sampling_percentage)
            # send the event to moesif via background so not blocking
            sending_background_thread = threading.Thread(target=sending_event)
            sending_background_thread.start()

        return response

    def update_user(self, user_profile):
        self.user.update_user(user_profile, self.api_client, self.DEBUG)

    def update_users_batch(self, user_profiles):
        self.user.update_users_batch(user_profiles, self.api_client, self.DEBUG)

    def update_company(self, company_profile):
        self.company.update_company(company_profile, self.api_client, self.DEBUG)

    def update_companies_batch(self, companies_profiles):
        self.company.update_companies_batch(companies_profiles, self.api_client, self.DEBUG)
