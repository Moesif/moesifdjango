from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpRequest, HttpResponse
from django.test.utils import override_settings
from django.test import RequestFactory

from django.contrib.auth.models import User

# Create your tests here.

import jsonpickle
from moesifdjango.middleware import moesif_middleware
from moesifdjango.masks import *

MIDDLEWARE_TEST_SETINGS = {
    'APPLICATION_ID': 'eyJhcHAiOiIzNDU6MSIsInZlciI6IjIuMCIsIm9yZyI6Ijg4OjIiLCJpYXQiOjE0NzcwMDgwMDB9.576_l8Bza-gOoKzBR4_qnKEQOi2UYHh_FAK9IoDdUgc',
    'REQUEST_HEADER_MASKS': ['header1', 'header2'],
    'REQUEST_BODY_MASKS': ['body1', 'body2'],
    'RESPONSE_HEADER_MASKS': ['header1', 'header2'],
    'RESPONSE_BODY_MASKS': ['body1', 'body2'],
    'LOCAL_DEBUG': True,
}

#    'LOCAL_MOESIF_BASEURL': 'http://192.168.0.5:8000/_moesif/api'
# prodution api baseurl is 'https://api.moesif.net'

class MoesifMiddlewareTest(TestCase):

    def setUp(self):
        self.request_factory = RequestFactory()
        self.user = User.objects.create_user(username='jacob', email='jacob@job.com', password='top_secret')

    @override_settings(MOESIF_MIDDLEWARE=MIDDLEWARE_TEST_SETINGS)
    def test_get_patched_middlesettings(self):
        def get_response(req):
            response_data = {}
            response_data['testing'] = 'basic'
            response_data['no_data'] = 'simplebody'
            response = HttpResponse(response_data)
            return response

        middleware = moesif_middleware(get_response)
        request = self.request_factory.get('/test/1')
        request.user = self.user
        response = middleware(request)
        self.assertEqual(response.status_code, 200);

class MaskTests(SimpleTestCase):
    def setUp(self):
        #Nothing to do here
        pass

    def test_mask_headers_with_none_headers(self):
        headers = None
        result = mask_headers(headers, ['mask1'])
        self.assertIsNone(result)

    def test_mask_headers_with_none_and_empty_masks(self):
        headers = {}
        headers['header1'] = 'header1value'
        headers['header2'] = 'header2value'
        masks = None
        result = mask_headers(headers, masks)
        self.assertEqual(headers, result)
        masks = []
        result = mask_headers(headers, [])
        self.assertEqual(headers, result)

    def test_mask_headers_with_masks(self):
        headers = {}
        headers = {}
        headers['header1'] = 'header1value'
        headers['header2'] = 'header2value'
        masks = ['header1', 'header3']
        result = mask_headers(headers, masks)
        self.assertEqual('header2value', result.get('header2'))
        self.assertIsNone(result.get('header1'))

    def test_mask_body_with_none_body(self):
        body = None
        result = mask_body(body, ['mask1'])
        self.assertIsNone(result)

    def test_mask_body_with_none_and_empty_masks(self):
        body = jsonpickle.decode('{"a": [1, 2, 3, {"b": 1}], "b": [1, 2, 3, {"c": 1}]}')
        masks = None
        result = mask_body(body, masks)
        self.assertEqual(body, result)
        masks = []
        result = mask_body(body, masks)
        self.assertEqual(body, result)

    def test_mask_body_with_deep_item(self):
        body = jsonpickle.decode("""
          {
            "a": [1, 2, 3, {"b": 1}],
            "b": [1, 2, 3, {"c": 1}],
            "c": 123,
            "d": "a string"
          }
          """)
        masks = ['c', 'd']
        result = mask_body(body, masks)
        self.assertIsNone(result.get('d'))
        self.assertIsNone(result['b'][3].get('c'))
