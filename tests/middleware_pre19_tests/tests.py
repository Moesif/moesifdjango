from django.test import SimpleTestCase, TestCase
from django.http import HttpResponse
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from moesifdjango.middleware_pre19 import MoesifMiddlewarePre19
from moesifdjango.masks import *
import jsonpickle


class MoesifMiddlewarePre19Test(TestCase):

    def setUp(self):
        self.request_factory = RequestFactory()
        self.user = User.objects.create_user(username='testpythonapiuser', email='test@test.com', password='top_secret')

    def test_get_patched_middlesettings(self):
        def get_response(req):
            response_data = {}
            response_data['testing'] = 'basic'
            response_data['no_data'] = 'simplebody'
            response = HttpResponse(response_data)
            return response

        middleware = MoesifMiddlewarePre19()
        request = self.request_factory.get('/api/acmeinc/items/83738/reviews')
        request.user = self.user
        request.moesif_req_time = timezone.now()
        request._mo_body = None
        response = middleware.process_response(request, get_response(request))
        self.assertEqual(response.status_code, 200)


class UpdateUserTests(SimpleTestCase):

    def testUpdateUser(self):
        MoesifMiddlewarePre19().update_user({
        'user_id': 'testpythonapiuser',
        'session_token': 'jkj9324-23489y5324-ksndf8-d9syf8',
        'metadata': {'email': 'abc@email.com', 'name': 'abcde', 'image': '1234'}
        })

class UpdateUsersBatchTest(SimpleTestCase):

    def testUpdateUsersBatch(self):
        MoesifMiddlewarePre19().update_users_batch([{
            'user_id': 'testpythonapiuser',
            'metadata': {'email': 'abc@email.com', 'name': 'abcdefg', 'image': '123'}
        }, {
            'user_id': 'testpythonapiuser1',
            'metadata': {'email': 'abc@email.com', 'name': 'abcdefg', 'image': '123'}
        }])


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
