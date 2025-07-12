from __future__ import print_function

import requests
import threading
import copy
import django
import logging
import random
import math
import queue
import json
from django.conf import settings
from django.utils import timezone
from moesifapi.moesif_api_client import *
from moesifapi.api_helper import *
from moesifapi.exceptions.api_exception import *
from moesifapi.models import *
from django.http import HttpRequest, HttpResponse
from .governance_rules import GovernanceRulesCacher
from .http_response_catcher import HttpResponseCatcher
from .masks import MaskData
from .client_ip import *
from .update_users import *
from .update_companies import *
from io import BytesIO
from moesifpythonrequest.start_capture.start_capture import StartCapture
from datetime import datetime, timedelta
from moesifapi.app_config.app_config import AppConfig
from .update_companies import Company
from .update_users import User
from .update_subscriptions import Subscription

from .client_ip import ClientIp
from .logger_helper import LoggerHelper
from .event_mapper import EventMapper
from .job_scheduler import JobScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import atexit
from .moesif_gov import *
from .parse_body import ParseBody
from apscheduler.schedulers.base import STATE_STOPPED


class moesif_middleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.
        self.middleware_settings = settings.MOESIF_MIDDLEWARE
        self.DEBUG = self.middleware_settings.get('LOCAL_DEBUG', False)
        self.LOG_BODY = self.middleware_settings.get('LOG_BODY', True)
        self.client = MoesifAPIClient(self.middleware_settings.get('APPLICATION_ID'))
        self.logger_helper = LoggerHelper()
        Configuration.BASE_URI = self.logger_helper.get_configuration_uri(self.middleware_settings, 'BASE_URI', 'LOCAL_MOESIF_BASEURL')
        Configuration.version = 'moesifdjango-python/2.3.13'
        if settings.MOESIF_MIDDLEWARE.get('CAPTURE_OUTGOING_REQUESTS', False):
            try:
                if self.DEBUG:
                    logger.info('Start capturing outgoing requests')
                # Start capturing outgoing requests
                StartCapture().start_capture_outgoing(settings.MOESIF_MIDDLEWARE)
            except:
                logger.warning('Error while starting to capture the outgoing events')
        self.api_version = self.middleware_settings.get('API_VERSION')
        self.api_client = self.client.api
        self.response_catcher = HttpResponseCatcher()
        self.api_client.http_call_back = self.response_catcher
        self.app_config = AppConfig()
        self.client_ip = ClientIp()
        self.event_mapper = EventMapper()
        self.job_scheduler = JobScheduler()
        self.mask_helper = MaskData()
        self.user = User()
        self.company = Company()
        self.subscription = Subscription()
        self.parse_body = ParseBody()

        self.config = self.app_config.get_config(self.api_client, self.DEBUG)
        self.gov_rule_helper = MoesifGovRuleHelper()
        self.entity_rules = self.gov_rule_helper.fetch_entity_rules_from_app_config(self.config, self.DEBUG)

        self.gov_rules_cacher = GovernanceRulesCacher(self.api_client)
        self.user_governance_rules, self.company_governance_rules, self.regex_governance_rules \
            = self.gov_rules_cacher.generate_rules_caching(self.DEBUG)

        self.sampling_percentage = 100
        self.config_etag = None
        self.rules_etag = None
        self.last_updated_time = datetime.utcnow()
        self._reset_scheduler()
        self.event_queue_size = self.middleware_settings.get('EVENT_QUEUE_SIZE', 1000000)
        self.mo_events_queue = queue.Queue(maxsize=self.event_queue_size)
        self.event_batch_size = self.middleware_settings.get('BATCH_SIZE', 25)
        try:
            if self.config:
                self.config_etag, self.sampling_percentage, self.last_updated_time = self.app_config.parse_configuration(
                    self.config, self.DEBUG)
        except Exception as e:
            if self.DEBUG:
                logger.info(f'Error while parsing application configuration on initialization: {str(e)}')

    # Function to listen to the send event job response
    def event_listener(self, event):
        if event.exception:
            if self.DEBUG:
                logger.info('Error reading response from the scheduled event job')
        else:
            if event.retval:
                response_config_etag, response_rules_etag, self.last_event_job_run_time = event.retval

                if response_config_etag:
                    if not self.config_etag or self.config_etag != response_config_etag:
                        try:
                            self.config, self.config_etag, self.sampling_percentage, self.last_updated_time = \
                                self.job_scheduler.fetch_app_config(self.config, self.config_etag,
                                                                    self.sampling_percentage,
                                                                    self.last_updated_time, self.api_client, self.DEBUG)
                            self.entity_rules = self.gov_rule_helper.fetch_entity_rules_from_app_config(self.config, self.DEBUG)

                        except Exception as ex:
                            if self.DEBUG:
                                logger.info(f'Error while updating the application configuration: {str(ex)}')

                if response_rules_etag:
                    if not self.rules_etag or self.rules_etag != response_rules_etag:
                        self.rules_etag = response_rules_etag
                        self.user_governance_rules, self.company_governance_rules, self.regex_governance_rules \
                            = self.gov_rules_cacher.generate_rules_caching(self.DEBUG)

    # Function to schedule send event job in async
    def schedule_event_background_job(self):
        try:
            if not self.scheduler:
                self.scheduler = BackgroundScheduler(daemon=True)
            if not self.scheduler.get_jobs():
                self.scheduler.add_listener(self.event_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
                self.scheduler.start()
                logger.info("Starting batch events job")
                self.scheduler.add_job(
                    func=lambda: self.job_scheduler.batch_events(self.api_client, self.mo_events_queue, self.DEBUG,
                                                                 self.event_batch_size),
                    trigger=IntervalTrigger(seconds=2),
                    id='moesif_events_batch_job',
                    name='Schedule events batch job every 2 second',
                    replace_existing=True)

                # Avoid passing logging message to the ancestor loggers
                logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
                logging.getLogger('apscheduler.executors.default').propagate = False

                # Exit handler when exiting the app
                atexit.register(lambda: self.job_scheduler.exit_handler(self.scheduler, self.DEBUG))
        except Exception as ex:
            if self.DEBUG:
                logger.info(f"Error when scheduling the job: {str(ex)}")

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        # Request Time
        req_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        if self.DEBUG:
            logger.info(f"event request time: {str(req_time)}")

        # Initialize Transaction Id
        transaction_id = None

        try:
            if self.LOG_BODY:
                request._mo_body = request.body
                request._stream = BytesIO(request.body)
                request._read_started = False
        except:
            request._mo_body = None

        if self.DEBUG:
            logger.info("raw body before getting response")

        response = self.get_response(request)
        # Code to be executed for each request/response after
        # the view is called.

        # Response Time
        rsp_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        if self.DEBUG:
            logger.info(f"event response time: {str(rsp_time)}")

        # Check if need to skip logging event
        skip_event_response = self.logger_helper.skip_event(request, response, self.middleware_settings, self.DEBUG)
        if skip_event_response:
            return skip_event_response

        # Request headers
        req_headers = self.logger_helper.parse_request_headers(request, self.middleware_settings, self.DEBUG)

        # Add transaction id to request headers
        req_headers, transaction_id = self.logger_helper.add_transaction_id_to_header(req_headers, transaction_id,
                                                                                      self.middleware_settings)

        # Prepare Request Body
        req_body, req_body_transfer_encoding = self.logger_helper.prepare_request_body(request, req_headers, self.LOG_BODY,
                                                                                       self.middleware_settings)
        # Fetch Ip Address
        ip_address = self.client_ip.get_client_ip(request)

        # Request URI
        uri = self.logger_helper.request_url(request)

        # Add transaction id to response headers
        if transaction_id:
            try:
                response._headers["x-moesif-transaction-id"] = ("X-Moesif-Transaction-Id", transaction_id)
            except AttributeError:
                response.headers["x-moesif-transaction-id"] = transaction_id

        # Parse Response headers
        rsp_headers = self.logger_helper.parse_response_headers(response, self.middleware_settings)

        # Prepare Response Body
        rsp_body, rsp_body_transfer_encoding = self.logger_helper.prepare_response_body(response, rsp_headers, self.LOG_BODY,
                                                                                        self.middleware_settings)

        # Prepare Event Request Model
        event_req = self.event_mapper.to_request(req_time, uri,request.method, self.api_version, ip_address,
                                                 req_headers, req_body, req_body_transfer_encoding)

        # Prepare Event Response Model
        event_rsp = self.event_mapper.to_response(rsp_time, response.status_code, rsp_headers, rsp_body,
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

        updated_Response = self.gov_rule_helper.govern_request(event_model,
                                                               user_id,
                                                               company_id,
                                                               req_body_transfer_encoding,  # could be json or base64
                                                               self.entity_rules,
                                                               self.user_governance_rules,
                                                               self.company_governance_rules,
                                                               self.regex_governance_rules,
                                                               self.DEBUG)

        if updated_Response:
            response.content = self.parse_body.encode_response_body(updated_Response.block_response_body)
            rsp_body, rsp_body_transfer_encoding = self.logger_helper.prepare_response_body(response,
                                                                                            updated_Response.block_response_headers,
                                                                                            self.LOG_BODY,
                                                                                            self.middleware_settings)

            response.status_code = updated_Response.block_response_status
            event_rsp = self.event_mapper.to_response(rsp_time, updated_Response.block_response_status,
                                                      updated_Response.block_response_headers, rsp_body,
                                                      rsp_body_transfer_encoding)
            # Prepare Event Model
            event_model = self.event_mapper.to_event(event_req, event_rsp, user_id, company_id, session_token,
                                                     metadata, updated_Response.blocked_by)

            # Mask Event Model
            event_model = self.logger_helper.mask_event(event_model, self.middleware_settings, self.DEBUG)

        # Create random percentage
        random_percentage = random.random() * 100
        self.sampling_percentage = self.app_config.get_sampling_percentage(event_model, json.loads(self.config.raw_body), user_id, company_id)
        if self.sampling_percentage >= random_percentage:
            event_model.weight = 1 if self.sampling_percentage == 0 else math.floor(100 / self.sampling_percentage)
            try:
                # Create scheduler if needed
                self._create_scheduler_if_needed()

                if self.DEBUG:
                    logger.info(f"Add Event to the queue: {str(self.mo_events_queue.qsize())}")
                self.mo_events_queue.put(event_model)
            except Exception as ex:
                if self.DEBUG:
                    logger.info(f"Error while adding event to the queue: {str(ex)}")

        return response

    def _reset_scheduler(self):
        """
        Private Method to reset scheduler to original `init` (aka null) state.
        """
        try:
            # try to  clean up before resetting
            self.scheduler.remove_job('moesif_events_batch_job')
            self.scheduler.shutdown()
        except Exception as es:
            # ignore because either schedule is null or job is null
            # cleanup is not needed
            pass
        finally:
            logger.info("----- Event scheduler will start on next event.")
            # Reset initialize it so that next time schedule job is called it gets created again.
            self.scheduler = None
            self.is_event_job_scheduled = False
            self.last_event_job_run_time = datetime(1970, 1, 1, 0, 0)  # Assuming job never ran, set it to epoch start time

    def _create_scheduler_if_needed(self):
        """
        Private method to create scheduler if:
           1. first time OR
           2. It exists but is in stopped state - so any subsequent add_job will throw exceptions.
        """
        # Check if scheduler exist but in stopped state (for some reason stopped by app/diff middlewares)
        # Reset it so that it can be restarted
        if self.scheduler and self.scheduler.state == STATE_STOPPED:
            self._reset_scheduler()

        # Create scheduler if needed
        if not self.is_event_job_scheduled and datetime.utcnow() > self.last_event_job_run_time + timedelta(minutes=5):
            try:
                self.schedule_event_background_job()
                self.is_event_job_scheduled = True
                self.last_event_job_run_time = datetime.utcnow()
            except Exception as ex:
                self.is_event_job_scheduled = False
                if self.DEBUG:
                    logger.info(f'Error while starting the event scheduler job in background: {str(ex)}')

    def update_user(self, user_profile):
        self.user.update_user(user_profile, self.api_client, self.DEBUG)

    def update_users_batch(self, user_profiles):
        self.user.update_users_batch(user_profiles, self.api_client, self.DEBUG)

    def update_company(self, company_profile):
        self.company.update_company(company_profile, self.api_client, self.DEBUG)

    def update_companies_batch(self, companies_profiles):
        self.company.update_companies_batch(companies_profiles, self.api_client, self.DEBUG)

    def update_subscription(self, subscription):
        self.subscription.update_subscription(subscription, self.api_client, self.DEBUG)

    def update_subscriptions_batch(self, subscriptions):
        self.subscription.update_subscriptions_batch(subscriptions, self.api_client, self.DEBUG)
