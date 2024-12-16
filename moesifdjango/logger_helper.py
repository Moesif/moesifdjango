from moesifapi.api_helper import *
from .masks import MaskData
from .parse_body import ParseBody
from django.http import HttpRequest, HttpResponse
import json
import base64
import re
import copy
import uuid
import logging

logger = logging.getLogger(__name__)


class LoggerHelper:
    def __init__(self):
        self.regex_http_ = re.compile(r'^HTTP_.+$')
        self.regex_content_type = re.compile(r'^CONTENT_TYPE$')
        self.regex_content_length = re.compile(r'^CONTENT_LENGTH$')
        self.mask_helper = MaskData()
        self.parse_body = ParseBody()

    @classmethod
    def flatten_to_string(cls, value):
        if type(value) == str:
            return value
        if value is None:
            return ''
        return APIHelper.json_serialize(value)

    @classmethod
    def mapper(cls, response, key):
        return copy.deepcopy(response[key])

    def parse_request_headers(self, request, middleware_settings, debug):
        req_headers = {}
        regex_http_start = re.compile('^HTTP_')
        try:
            for header in request.META:
                if self.regex_http_.match(header) or self.regex_content_type.match(
                        header) or self.regex_content_length.match(header):
                    normalized_header = regex_http_start.sub('', header)
                    normalized_header = normalized_header.replace('_', '-')
                    req_headers[normalized_header] = request.META[header]
            req_headers = self.mask_helper.mask_headers(req_headers, middleware_settings.get('REQUEST_HEADER_MASKS'))
        except Exception as inst:
            if debug:
                logger.info(f"error encountered while copying request header: {str(inst)}")
            req_headers = {}

        if debug:
            logger.info("checking request meta %d " % len(request.META))
            for x in request.META:
                logger.info(f'{x}: {request.META[x]}')
            logger.info("about to print headers %d " % len(req_headers))
            for x in req_headers:
                logger.info(f'{x}: {req_headers[x]}')

        req_headers = {k: self.flatten_to_string(v) for k, v in req_headers.items()}
        return req_headers

    def prepare_request_body(self, request, req_headers, log_body, middleware_settings):
        req_body = None
        req_body_transfer_encoding = None
        if log_body and request._mo_body:
            if isinstance(request._mo_body, str):
                req_body, req_body_transfer_encoding = self.parse_body.parse_string_body(request._mo_body,
                                                                                         self.parse_body.transform_headers(
                                                                                             req_headers),
                                                                                         middleware_settings.get(
                                                                                             'REQUEST_BODY_MASKS'))
            else:
                req_body, req_body_transfer_encoding = self.parse_body.parse_bytes_body(request._mo_body,
                                                                                        self.parse_body.transform_headers(
                                                                                            req_headers),
                                                                                        middleware_settings.get(
                                                                                            'REQUEST_BODY_MASKS'))
        return req_body, req_body_transfer_encoding

    def parse_response_headers(self, response, middleware_settings):
        # a little hacky, using _headers, which is intended as a private variable.
        try:
            rsp_headers = {k: self.mapper(response, k) for k, v in response._headers.items()}
        except AttributeError:
            rsp_headers = {k: self.mapper(response, k) for k, v in response.headers.items()}
        return self.mask_helper.mask_headers(rsp_headers, middleware_settings.get('RESPONSE_HEADER_MASKS'))

    def prepare_response_body(self, response, rsp_headers, log_body, middleware_settings):
        rsp_body = None
        rsp_body_transfer_encoding = None
        if log_body and isinstance(response, HttpResponse) and response.content:
            if isinstance(response.content, str):
                rsp_body, rsp_body_transfer_encoding = self.parse_body.parse_string_body(response.content,
                                                                                         self.parse_body.transform_headers(
                                                                                             rsp_headers),
                                                                                         middleware_settings.get(
                                                                                             'RESPONSE_BODY_MASKS'))
            else:
                rsp_body, rsp_body_transfer_encoding = self.parse_body.parse_bytes_body(response.content,
                                                                                        self.parse_body.transform_headers(
                                                                                            rsp_headers),
                                                                                        middleware_settings.get(
                                                                                            'RESPONSE_BODY_MASKS'))
        return rsp_body, rsp_body_transfer_encoding

    @classmethod
    def request_url(cls, request):
        return request.scheme + "://" + request.get_host() + request.get_full_path()

    @classmethod
    def add_transaction_id_to_header(cls, req_headers, transaction_id, middleware_settings):
        capture_transaction_id = middleware_settings.get('DISABLE_TRANSACTION_ID', False)
        if not capture_transaction_id:
            req_trans_id = req_headers.get("X-MOESIF-TRANSACTION-ID", None)
            if req_trans_id:
                transaction_id = req_trans_id
                if not transaction_id:
                    transaction_id = str(uuid.uuid4())
            else:
                transaction_id = str(uuid.uuid4())
            # Add transaction id to the request header
            req_headers["X-MOESIF-TRANSACTION-ID"] = transaction_id
        return req_headers, transaction_id

    @classmethod
    def transform_token(cls, token):
        if not isinstance(token, str):
            token = token.decode('utf-8')
        return token

    @classmethod
    def fetch_token(cls, token, token_type):
        return token.split(token_type, 1)[1].strip()

    @classmethod
    def split_token(cls, token):
        return token.split('.')

    def parse_authorization_header(self, token, field, debug):
        try:
            # Fix the padding issue before decoding
            token += '=' * (-len(token) % 4)
            # Decode the payload
            base64_decode = base64.b64decode(token)
            # Transform token to string to be compatible with Python 2 and 3
            base64_decode = self.transform_token(base64_decode)
            # Convert the payload to json
            json_decode = json.loads(base64_decode)
            # Convert keys to lowercase
            json_decode = {k.lower(): v for k, v in json_decode.items()}
            # Check if field is present in the body
            if field in json_decode:
                # Fetch user Id
                return str(json_decode[field])
        except Exception as e:
            if debug:
                logger.info(f"Error while parsing authorization header to fetch user id: {str(e)}")
        return None

    def get_user_id(self, middleware_settings, request, response, request_headers, debug):
        user_id = None
        try:
            identify_user = middleware_settings.get('IDENTIFY_USER', None)
            if identify_user is not None:
                user_id = identify_user(request, response)
            if not user_id:
                if request.user and request.user.is_authenticated and request.user.username:
                    return request.user.username
                else:
                    # Transform request headers keys to lower case
                    request_headers = {k.lower(): v for k, v in request_headers.items()}
                    # Fetch the auth header name from the config
                    auth_header_names = middleware_settings.get('AUTHORIZATION_HEADER_NAME', 'authorization').lower()
                    # Split authorization header name by comma
                    auth_header_names = [x.strip() for x in auth_header_names.split(',')]
                    # Fetch the header name available in the request header
                    token = None
                    for auth_name in auth_header_names:
                        # Check if the auth header name in request headers
                        if auth_name in request_headers:
                            # Fetch the token from the request headers
                            token = request_headers[auth_name]
                            # Split the token by comma
                            token = [x.strip() for x in token.split(',')]
                            # Fetch the first available header
                            if len(token) >= 1:
                                token = token[0]
                            else:
                                token = None
                            break
                    # Fetch the field from the config
                    field = middleware_settings.get('AUTHORIZATION_USER_ID_FIELD', 'sub').lower()
                    # Check if the auth header name in request headers
                    if token:
                        # Check if token is of type Bearer
                        if 'Bearer' in token:
                            # Fetch the bearer token
                            token = self.fetch_token(token, 'Bearer')
                            # Split the bearer token by dot(.)
                            split_token = self.split_token(token)
                            # Check if payload is not None
                            if len(split_token) >= 3 and split_token[1]:
                                # Parse and set user Id
                                user_id = self.parse_authorization_header(split_token[1], field, debug)
                        # Check if token is of type Basic
                        elif 'Basic' in token:
                            # Fetch the basic token
                            token = self.fetch_token(token, 'Basic')
                            # Decode the token
                            decoded_token = base64.b64decode(token)
                            # Transform token to string to be compatible with Python 2 and 3
                            decoded_token = self.transform_token(decoded_token)
                            # Fetch and set the user Id
                            user_id = decoded_token.split(':', 1)[0].strip()
                        # Check if token is of user-defined custom type
                        else:
                            # Split the token by dot(.)
                            split_token = self.split_token(token)
                            # Check if payload is not None
                            if len(split_token) > 1 and split_token[1]:
                                # Parse and set user Id
                                user_id = self.parse_authorization_header(split_token[1], field, debug)
                            else:
                                # Parse and set user Id
                                user_id = self.parse_authorization_header(token, field, debug)
        except Exception as e:
            if debug:
                logger.info(f"can not execute identify_user function, please check moesif settings: {str(e)}")
        return user_id

    @classmethod
    def get_company_id(cls, middleware_settings, request, response, debug):
        company_id = None
        try:
            identify_company = middleware_settings.get('IDENTIFY_COMPANY', None)
            if identify_company is not None:
                company_id = identify_company(request, response)
        except:
            if debug:
                logger.info("can not execute identify_company function, please check moesif settings.")
        return company_id

    @classmethod
    def get_metadata(cls, middleware_settings, request, response, debug):
        metadata = None
        try:
            get_metadata = middleware_settings.get('GET_METADATA', None)
            if get_metadata is not None:
                metadata = get_metadata(request, response)
        except:
            if debug:
                logger.info("can not execute get_metadata function, please check moesif settings.")
        return metadata

    @classmethod
    def get_session_token(cls, middleware_settings, request, response, debug):
        session_token = None
        try:
            if request.session and request.session.session_key:
                session_token = request.session.session_key
            else:
                get_session_token = middleware_settings.get('GET_SESSION_TOKEN', None)
                if get_session_token is not None:
                    session_token = get_session_token(request, response)
        except:
            if debug:
                logger.info("Can not execute get_session_token function. Please check moesif settings.")
        return session_token

    @classmethod
    def skip_event(cls, request, response, middleware_settings, debug):
        try:
            skip_event = middleware_settings.get('SKIP', None)
            if skip_event is not None:
                if skip_event(request, response):
                    return response
        except:
            if debug:
                logger.info("Having difficulty executing skip_event function. Please check moesif settings.")
            return None

    @classmethod
    def mask_event(cls, event_model, middleware_settings, debug):
        try:
            mask_event_model = middleware_settings.get('MASK_EVENT_MODEL', None)
            if mask_event_model is not None:
                event_model = mask_event_model(event_model)
        except:
            if debug:
                logger.info("Can not execute mask_event_model function. Please check moesif settings.")
        return event_model

    # Function to get configuration uri
    @classmethod
    def get_configuration_uri(cls, settings, field, deprecated_field):
        uri = settings.get(field)
        if uri:
            return uri
        else:
            return settings.get(deprecated_field, 'https://api.moesif.net')
