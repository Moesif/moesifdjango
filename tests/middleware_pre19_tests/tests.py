from django.test import SimpleTestCase, TestCase
from django.http import HttpResponse
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from moesifdjango.middleware_pre19 import MoesifMiddlewarePre19
from moesifdjango.masks import MaskData
import jsonpickle


class MoesifMiddlewarePre19Test(TestCase):

    def setUp(self):
        self.request_factory = RequestFactory()
        self.user = User.objects.create_user(username='my_user_id', email='test@test.com', password='top_secret')

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
        'user_id': '12345',
        'company_id' : '67890',
        'session_token': 'jkj9324-23489y5324-ksndf8-d9syf8',
        'metadata': {'email': 'abc@email.com', 'name': 'abcde', 'image': '1234'},
        'campaign': {'utm_source': 'Newsletter', 'utm_medium': 'Email'}
        })

class UpdateUsersBatchTest(SimpleTestCase):

    def testUpdateUsersBatch(self):
        MoesifMiddlewarePre19().update_users_batch([{
            'user_id': '12345',
            'company_id' : '67890',
            'metadata': {'email': 'abc@email.com', 'name': 'abcdefg', 'image': '123'}
        }, {
            'user_id': '1234',
            'company_id' : '6789',
            'metadata': {'email': 'abc@email.com', 'name': 'abcdefg', 'image': '123'}
        }])

class UpdateCompanyTest(SimpleTestCase):

    def testUpdateCompany(self):
        MoesifMiddlewarePre19().update_company({
        'company_id': '12345',
        'company_domain': 'acmeinc.com',
        'metadata': {'email': 'abc@email.com', 'name': 'abcde', 'image': '1234'},
        'campaign': {'utm_source': 'Adwords', 'utm_medium': 'Twitter'}
        })

class UpdateCompaniesBatchTest(SimpleTestCase):

    def testUpdateCompaniesBatch(self):
        MoesifMiddlewarePre19().update_companies_batch([{
            'company_id': '12345',
            'company_domain': 'nowhere.com',
            'metadata': {'email': 'abc@email.com', 'name': 'abcdefg', 'image': '123'}
        }, {
            'company_id': '67890',
            'company_domain': 'acmeinc.com',
            'metadata': {'email': 'abc@email.com', 'name': 'abcdefg', 'image': '123'}
        }])


class MaskTests(SimpleTestCase):
    def setUp(self):
        self.mask_helper = MaskData()

    def test_mask_headers_with_none_headers(self):
        headers = None
        result = self.mask_helper.mask_headers(headers, ['mask1'])
        self.assertIsNone(result)

    def test_mask_headers_with_none_and_empty_masks(self):
        headers = {}
        headers['header1'] = 'header1value'
        headers['header2'] = 'header2value'
        masks = None
        result = self.mask_helper.mask_headers(headers, masks)
        self.assertEqual(headers, result)
        masks = []
        result = self.mask_helper.mask_headers(headers, [])
        self.assertEqual(headers, result)

    def test_mask_headers_with_masks(self):
        headers = {}
        headers = {}
        headers['header1'] = 'header1value'
        headers['header2'] = 'header2value'
        masks = ['header1', 'header3']
        result = self.mask_helper.mask_headers(headers, masks)
        self.assertEqual('header2value', result.get('header2'))
        self.assertIsNone(result.get('header1'))

    def test_mask_body_with_none_body(self):
        body = None
        result = self.mask_helper.mask_body(body, ['mask1'])
        self.assertIsNone(result)

    def test_mask_body_with_none_and_empty_masks(self):
        body = jsonpickle.decode('{"a": [1, 2, 3, {"b": 1}], "b": [1, 2, 3, {"c": 1}]}')
        masks = None
        result = self.mask_helper.mask_body(body, masks)
        self.assertEqual(body, result)
        masks = []
        result = self.mask_helper.mask_body(body, masks)
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
        result = self.mask_helper.mask_body(body, masks)
        self.assertIsNone(result.get('d'))
        self.assertIsNone(result['b'][3].get('c'))
