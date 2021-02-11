from __future__ import print_function

import requests
import threading
import copy
import django
import logging
import random
import math
import queue
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
from .update_companies import Company
from .update_users import User
from .client_ip import ClientIp
from .logger_helper import LoggerHelper
from .event_mapper import EventMapper
from .job_scheduler import JobScheduler

CELERY = False
if settings.MOESIF_MIDDLEWARE.get('USE_CELERY', False):
    try:
        import celery
        from .tasks import async_client_create_event
        from kombu import Connection
        try:
            BROKER_URL = settings.BROKER_URL
            if BROKER_URL:
                CELERY = True
            else:
                CELERY = False
        except AttributeError:
            BROKER_URL = settings.MOESIF_MIDDLEWARE.get('CELERY_BROKER_URL', None)
            if BROKER_URL:
                CELERY = True
            else:
                print("USE_CELERY flag was set to TRUE, but BROKER_URL not found")
                CELERY = False

        try:
            conn = Connection(BROKER_URL)
            simple_queue = conn.SimpleQueue('moesif_events_queue')
        except:
            print("Error while connecting to - {0}".format(BROKER_URL))

    except:
        print("USE_CELERY flag was set to TRUE, but celery package not found.")
        CELERY = False


class moesif_middleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.
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
        self.response_catcher = HttpResponseCatcher()
        self.api_client.http_call_back = self.response_catcher
        self.app_config = AppConfig()
        self.client_ip = ClientIp()
        self.logger_helper = LoggerHelper()
        self.event_mapper = EventMapper()
        self.job_scheduler = JobScheduler()
        self.mask_helper = MaskData()
        self.user = User()
        self.company = Company()
        self.config = self.app_config.get_config(self.api_client, self.DEBUG)
        self.sampling_percentage = 100
        self.config_etag = None
        self.last_updated_time = datetime.utcnow()
        self.mo_events_queue = queue.Queue()
        self.event_batch_size = self.middleware_settings.get('BATCH_SIZE', 25)
        self.is_event_job_scheduled = False
        self.is_config_job_scheduled = False
        try:
            if self.config:
                self.config_etag, self.sampling_percentage, self.last_updated_time = self.app_config.parse_configuration(self.config, self.DEBUG)
        except Exception as e:
            if self.DEBUG:
                print('Error while parsing application configuration on initialization')
                print(str(e))
        try:
            if not CELERY:
                self.schedule_event_background_job()
                self.is_event_job_scheduled = True
        except Exception as ex:
            self.is_event_job_scheduled = False
            if self.DEBUG:
                print('Error while starting the event scheduler job in background')
                print(str(ex))

    # Function to listen to the send event job response
    def event_listener(self, event):
        if event.exception:
            if self.DEBUG:
                print('Error reading response from the scheduled event job')
        else:
            if event.retval:
                if event.retval is not None \
                        and self.config_etag is not None \
                        and self.config_etag != event.retval \
                        and datetime.utcnow() > self.last_updated_time + timedelta(minutes=5):
                    try:
                        self.fetch_app_config()
                    except Exception as ex:
                        if self.DEBUG:
                            print('Error while updating the application configuration')
                            print(str(ex))

    # Function to schedule send event job in async
    def schedule_event_background_job(self):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
            import atexit

            scheduler = BackgroundScheduler(daemon=True)
            scheduler.add_listener(self.event_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
            scheduler.start()
            try:
                scheduler.add_job(
                    func=lambda: self.job_scheduler.batch_events(self.api_client, self.mo_events_queue, self.DEBUG, self.event_batch_size),
                    trigger=IntervalTrigger(seconds=2),
                    id='moesif_events_batch_job',
                    name='Schedule events batch job every 2 second',
                    replace_existing=True)

                # Exit handler when exiting the app
                atexit.register(lambda: self.job_scheduler.exit_handler(scheduler, self.DEBUG))
            except Exception as ex:
                if self.DEBUG:
                    print("Error while calling async function")
                    print(str(ex))
        except Exception as e:
            if self.DEBUG:
                print("Error when scheduling the job")
                print(str(e))

    # Function to fetch application config
    def fetch_app_config(self):
        try:
            self.config = self.app_config.get_config(self.api_client, self.DEBUG)
            if self.config:
                self.config_etag, self.sampling_percentage, self.last_updated_time = self.app_config.parse_configuration(self.config, self.DEBUG)
        except Exception as e:
            if self.DEBUG:
                print('Error while fetching the application configuration')
                print(str(e))

    def schedule_app_config_job(self):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            import atexit

            scheduler = BackgroundScheduler(daemon=True)
            scheduler.start()
            try:
                scheduler.add_job(
                    func=lambda: self.fetch_app_config(),
                    trigger=IntervalTrigger(minutes=5),
                    id='moesif_app_config_job',
                    name='Schedule app config job every 5 minutes',
                    replace_existing=True)

                # Avoid passing logging message to the ancestor loggers
                logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
                logging.getLogger('apscheduler.executors.default').propagate = False

                # Exit handler when exiting the app
                atexit.register(lambda: self.job_scheduler.exit_handler(scheduler, self.DEBUG))
            except Exception as ex:
                if self.DEBUG:
                    print("Error while calling app config async function")
                    print(str(ex))
        except Exception as e:
            if self.DEBUG:
                print("Error when scheduling the app config job")
                print(str(e))

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        # Initialize Transaction Id
        transaction_id = None

        # Request Time
        req_time = timezone.now()

        try:
            request._mo_body = request.body
            request._stream = BytesIO(request.body)
            request._read_started = False
        except:
            request._mo_body = None

        if self.DEBUG:
            print("raw body before getting response")

        response = self.get_response(request)
        # Code to be executed for each request/response after
        # the view is called.

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
            response._headers["x-moesif-transaction-id"] = ("X-Moesif-Transaction-Id", transaction_id)

        # Parse Response headers
        rsp_headers = self.logger_helper.parse_response_headers(response, self.middleware_settings)

        # Prepare Response Body
        rsp_body, rsp_body_transfer_encoding = self.logger_helper.prepare_response_body(response, rsp_headers, self.LOG_BODY,
                                                                                        self.middleware_settings)
        # Response Time
        rsp_time = timezone.now()

        # Prepare Event Request Model
        event_req = self.event_mapper.to_request(req_time.isoformat(), uri,request.method, self.api_version, ip_address,
                                                 req_headers, req_body, req_body_transfer_encoding)

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
            try:
                message = event_model.to_dictionary()
                simple_queue.put(message)
                if self.DEBUG:
                    print("Event added to the queue")
            except Exception as exc:
                if self.DEBUG:
                    print("Error while adding event to the queue")
                    print(str(exc))

        # Create random percentage
        random_percentage = random.random() * 100
        self.sampling_percentage = self.app_config.get_sampling_percentage(self.config, user_id, company_id)
        if self.sampling_percentage >= random_percentage:
            event_model.weight = 1 if self.sampling_percentage == 0 else math.floor(100 / self.sampling_percentage)
            if CELERY:
                sending_event()
                try:
                    if not self.is_config_job_scheduled:
                        self.schedule_app_config_job()
                        self.is_config_job_scheduled = True
                except Exception as e:
                    if self.DEBUG:
                        print('Error while starting the app config scheduler job in background')
                        print(str(e))
                    self.is_config_job_scheduled = False
            else:
                try:
                    if self.is_event_job_scheduled:
                        if self.DEBUG:
                            print("Add Event to the queue")
                        self.mo_events_queue.put(event_model)
                    else:
                        self.schedule_event_background_job()
                        self.is_event_job_scheduled = True
                except Exception as ex:
                    if self.DEBUG:
                        print("Error while adding event to the queue")
                        print(str(ex))
                    self.is_event_job_scheduled = False

        return response

    def update_user(self, user_profile):
        self.user.update_user(user_profile, self.api_client, self.DEBUG)

    def update_users_batch(self, user_profiles):
        self.user.update_users_batch(user_profiles, self.api_client, self.DEBUG)

    def update_company(self, company_profile):
        self.company.update_company(company_profile, self.api_client, self.DEBUG)

    def update_companies_batch(self, companies_profiles):
        self.company.update_companies_batch(companies_profiles, self.api_client, self.DEBUG)
