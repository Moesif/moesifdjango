from __future__ import print_function

import requests
import threading
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
from .masks import MaskData
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
from .logger_helper import LoggerHelper
from .event_mapper import EventMapper

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
        self.app_config = AppConfig()
        self.parse_body = ParseBody()
        self.client_ip = ClientIp()
        self.logger_helper = LoggerHelper()
        self.event_mapper = EventMapper()
        self.mask_helper = MaskData()
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

    @classmethod
    def process_request(cls, request):
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

        # Check if need to skip logging event
        skip_event_response = self.logger_helper.skip_event(request, response, self.middleware_settings, self.DEBUG)
        if skip_event_response:
            return skip_event_response
        # Request headers
        req_headers = self.logger_helper.parse_request_headers(request, self.middleware_settings, self.DEBUG)

        # Add transaction id to request headers
        req_headers, self.transaction_id = self.logger_helper.add_transaction_id_to_header(req_headers, self.transaction_id,
                                                                                      self.middleware_settings)

        # Prepare Request Body
        req_body, req_body_transfer_encoding = self.logger_helper.prepare_request_body(request, req_headers,
                                                                                       self.LOG_BODY,
                                                                                       self.middleware_settings)
        # Fetch Ip Address
        ip_address = self.client_ip.get_client_ip(request)

        # Request URI
        uri = self.logger_helper.request_url(request)

        # Add transaction id to request headers
        if self.transaction_id:
            response._headers["x-moesif-transaction-id"] = ("X-Moesif-Transaction-Id", self.transaction_id)

        # Parse Response headers
        rsp_headers = self.logger_helper.parse_response_headers(response, self.middleware_settings)

        # Prepare Response Body
        rsp_body, rsp_body_transfer_encoding = self.logger_helper.prepare_response_body(response, rsp_headers,
                                                                                        self.LOG_BODY,
                                                                                        self.middleware_settings)

        # Response Time
        rsp_time = timezone.now()

        # Prepare Event Request Model
        event_req = self.event_mapper.to_request(req_time.isoformat(), uri, request.method, self.api_version,
                                                 ip_address, req_headers, req_body, req_body_transfer_encoding)

        # Prepare Event Response Model
        event_rsp = self.event_mapper.to_response(rsp_time.isoformat(), response.status_code, rsp_headers, rsp_body,
                                                  rsp_body_transfer_encoding)

        # User Id
        user_id = self.logger_helper.get_user_id(self.middleware_settings, request, response, req_headers, self.DEBUG)

        # Company Id
        company_id = self.logger_helper.get_company_id(self.middleware_settings, request, response, self.DEBUG)

        # Event Metadata
        metadata = self.logger_helper.get_metadata(self.middleware_settings, request, response, self.DEBUG)

        # Session Token
        session_token = self.logger_helper.get_session_token(self.middleware_settings, request, response, self.DEBUG)

        # Prepare Event Model
        event_model = self.event_mapper.to_event(event_req, event_rsp, user_id, company_id, session_token, metadata)

        # Mask Event Model
        event_model = self.logger_helper.mask_event(event_model, self.middleware_settings, self.DEBUG)

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

        self.sampling_percentage = self.app_config.get_sampling_percentage(self.config, user_id, company_id)
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
