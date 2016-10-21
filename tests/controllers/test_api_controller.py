# -*- coding: utf-8 -*-

"""
    tests.controllers.test_api_controller


"""

import jsonpickle
from .controller_test_base import *
from moesifapi.models import *
from datetime import *

class ApiControllerTests(ControllerTestBase):

    @classmethod
    def setUpClass(cls):
        super(ApiControllerTests, cls).setUpClass()
        cls.controller = cls.api_client.api

    # Add Single Event via Injestion API
    def test_add_event(self):
        # Parameters for the API call


        req_headers = APIHelper.json_deserialize("""  {
    			"Host": "api.acmeinc.com",
    			"Accept": "*/*",
    			"Connection": "Keep-Alive",
    			"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.0.2; C6906 Build/14.5.A.0.242)",
    			"Content-Type": "application/json",
    			"Content-Length": "126",
    			"Accept-Encoding": "gzip"
    		} """)

        req_body = APIHelper.json_deserialize( """{
    			"items": [
    				{
    					"type": 1,
    					"id": "fwfrf"
    				},
    				{
    					"type": 2,
    					"id": "d43d3f"
    				}
    			]
    		}""")

        rsp_headers = APIHelper.json_deserialize("""  {
    			"Date": "Tue, 23 Aug 2016 23:46:49 GMT",
    			"Vary": "Accept-Encoding",
    			"Pragma": "no-cache",
    			"Expires": "-1",
    			"Content-Type": "application/json; charset=utf-8",
    			"Cache-Control": "no-cache"
    		} """)

        rsp_body = APIHelper.json_deserialize( """{
    			"Error": "InvalidArgumentException",
    			"Message": "Missing field field_a"
    		}""")


        event_req = EventRequestModel(time = datetime.utcnow() - timedelta(seconds=-1),
            uri = "https://api.acmeinc.com/items/reviews/",
            verb = "PATCH",
            api_version = "1.1.0",
            ip_address = "61.48.220.123",
            headers = req_headers,
            body = req_body)

        event_rsp = EventResponseModel(time = datetime.utcnow(),
            status = 500,
            headers = rsp_headers,
            body = rsp_body)

        event_model = EventModel(request = event_req,
            response = event_rsp,
            user_id = "my_user_id",
            session_token = "23jdf0owekfmcn4u3qypxg09w4d8ayrcdx8nu2ng]s98y18cx98q3yhwmnhcfx43f")


        # Perform the API call through the SDK function
        self.controller.create_event(event_model)

        # Test response code
        self.assertEquals(self.response_catcher.response.status_code, 201)

    # Add Batched Events via Ingestion API
    def test_add_batched_events(self):
        # Parameters for the API call
        body = APIHelper.json_deserialize('[{ 					"request": { 						"time": "2016-09-09T04:45:42.914", 						"uri": "https://api.acmeinc.com/items/reviews/", 						"verb": "PATCH", 						"api_version": "1.1.0", 						"ip_address": "61.48.220.123", 						"headers": { 							"Host": "api.acmeinc.com", 							"Accept": "*/*", 							"Connection": "Keep-Alive", 							"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.0.2; C6906 Build/14.5.A.0.242)", 							"Content-Type": "application/json", 							"Content-Length": "126", 							"Accept-Encoding": "gzip" 						}, 						"body": { 							"items": [ 								{ 									"direction_type": 1, 									"discovery_id": "fwfrf", 									"liked": false 								}, 								{ 									"direction_type": 2, 									"discovery_id": "d43d3f", 									"liked": true 								} 							] 						} 					}, 					"response": { 						"time": "2016-09-09T04:45:42.914", 						"status": 500, 						"headers": { 							"Date": "Tue, 23 Aug 2016 23:46:49 GMT", 							"Vary": "Accept-Encoding", 							"Pragma": "no-cache", 							"Expires": "-1", 							"Content-Type": "application/json; charset=utf-8", 							"X-Powered-By": "ARR/3.0", 							"Cache-Control": "no-cache", 							"Arr-Disable-Session-Affinity": "true" 						}, 						"body": { 							"Error": "InvalidArgumentException", 							"Message": "Missing field field_a" 						} 					}, 					"user_id": "mndug437f43", 					"session_token": "23jdf0owekfmcn4u3qypxg09w4d8ayrcdx8nu2ng]s98y18cx98q3yhwmnhcfx43f" 					 }, { 					"request": { 						"time": "2016-09-09T04:46:42.914", 						"uri": "https://api.acmeinc.com/items/reviews/", 						"verb": "PATCH", 						"api_version": "1.1.0", 						"ip_address": "61.48.220.123", 						"headers": { 							"Host": "api.acmeinc.com", 							"Accept": "*/*", 							"Connection": "Keep-Alive", 							"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.0.2; C6906 Build/14.5.A.0.242)", 							"Content-Type": "application/json", 							"Content-Length": "126", 							"Accept-Encoding": "gzip" 						}, 						"body": { 							"items": [ 								{ 									"direction_type": 1, 									"discovery_id": "fwfrf", 									"liked": false 								}, 								{ 									"direction_type": 2, 									"discovery_id": "d43d3f", 									"liked": true 								} 							] 						} 					}, 					"response": { 						"time": "2016-09-09T04:46:42.914", 						"status": 500, 						"headers": { 							"Date": "Tue, 23 Aug 2016 23:46:49 GMT", 							"Vary": "Accept-Encoding", 							"Pragma": "no-cache", 							"Expires": "-1", 							"Content-Type": "application/json; charset=utf-8", 							"X-Powered-By": "ARR/3.0", 							"Cache-Control": "no-cache", 							"Arr-Disable-Session-Affinity": "true" 						}, 						"body": { 							"Error": "InvalidArgumentException", 							"Message": "Missing field field_a" 						} 					}, 					"user_id": "mndug437f43", 					"session_token": "23jdf0owekfmcn4u3qypxg09w4d8ayrcdx8nu2ng]s98y18cx98q3yhwmnhcfx43f" 					 }, { 					"request": { 						"time": "2016-09-09T04:47:42.914", 						"uri": "https://api.acmeinc.com/items/reviews/", 						"verb": "PATCH", 						"api_version": "1.1.0", 						"ip_address": "61.48.220.123", 						"headers": { 							"Host": "api.acmeinc.com", 							"Accept": "*/*", 							"Connection": "Keep-Alive", 							"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.0.2; C6906 Build/14.5.A.0.242)", 							"Content-Type": "application/json", 							"Content-Length": "126", 							"Accept-Encoding": "gzip" 						}, 						"body": { 							"items": [ 								{ 									"direction_type": 1, 									"discovery_id": "fwfrf", 									"liked": false 								}, 								{ 									"direction_type": 2, 									"discovery_id": "d43d3f", 									"liked": true 								} 							] 						} 					}, 					"response": { 						"time": "2016-09-09T04:47:42.914", 						"status": 500, 						"headers": { 							"Date": "Tue, 23 Aug 2016 23:46:49 GMT", 							"Vary": "Accept-Encoding", 							"Pragma": "no-cache", 							"Expires": "-1", 							"Content-Type": "application/json; charset=utf-8", 							"X-Powered-By": "ARR/3.0", 							"Cache-Control": "no-cache", 							"Arr-Disable-Session-Affinity": "true" 						}, 						"body": { 							"Error": "InvalidArgumentException", 							"Message": "Missing field field_a" 						} 					}, 					"user_id": "mndug437f43", 					"session_token": "23jdf0owekfmcn4u3qypxg09w4d8ayrcdx8nu2ng]s98y18cx98q3yhwmnhcfx43f" 					 }, { 					"request": { 						"time": "2016-09-09T04:48:42.914", 						"uri": "https://api.acmeinc.com/items/reviews/", 						"verb": "PATCH", 						"api_version": "1.1.0", 						"ip_address": "61.48.220.123", 						"headers": { 							"Host": "api.acmeinc.com", 							"Accept": "*/*", 							"Connection": "Keep-Alive", 							"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.0.2; C6906 Build/14.5.A.0.242)", 							"Content-Type": "application/json", 							"Content-Length": "126", 							"Accept-Encoding": "gzip" 						}, 						"body": { 							"items": [ 								{ 									"direction_type": 1, 									"discovery_id": "fwfrf", 									"liked": false 								}, 								{ 									"direction_type": 2, 									"discovery_id": "d43d3f", 									"liked": true 								} 							] 						} 					}, 					"response": { 						"time": "2016-09-09T04:48:42.914", 						"status": 500, 						"headers": { 							"Date": "Tue, 23 Aug 2016 23:46:49 GMT", 							"Vary": "Accept-Encoding", 							"Pragma": "no-cache", 							"Expires": "-1", 							"Content-Type": "application/json; charset=utf-8", 							"X-Powered-By": "ARR/3.0", 							"Cache-Control": "no-cache", 							"Arr-Disable-Session-Affinity": "true" 						}, 						"body": { 							"Error": "InvalidArgumentException", 							"Message": "Missing field field_a" 						} 					}, 					"user_id": "mndug437f43", 					"session_token": "exfzweachxjgznvKUYrxFcxv]s98y18cx98q3yhwmnhcfx43f" 					 }, { 					"request": { 						"time": "2016-09-09T04:49:42.914", 						"uri": "https://api.acmeinc.com/items/reviews/", 						"verb": "PATCH", 						"api_version": "1.1.0", 						"ip_address": "61.48.220.123", 						"headers": { 							"Host": "api.acmeinc.com", 							"Accept": "*/*", 							"Connection": "Keep-Alive", 							"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.0.2; C6906 Build/14.5.A.0.242)", 							"Content-Type": "application/json", 							"Content-Length": "126", 							"Accept-Encoding": "gzip" 						}, 						"body": { 							"items": [ 								{ 									"direction_type": 1, 									"discovery_id": "fwfrf", 									"liked": false 								}, 								{ 									"direction_type": 2, 									"discovery_id": "d43d3f", 									"liked": true 								} 							] 						} 					}, 					"response": { 						"time": "2016-09-09T04:49:42.914", 						"status": 500, 						"headers": { 							"Date": "Tue, 23 Aug 2016 23:46:49 GMT", 							"Vary": "Accept-Encoding", 							"Pragma": "no-cache", 							"Expires": "-1", 							"Content-Type": "application/json; charset=utf-8", 							"X-Powered-By": "ARR/3.0", 							"Cache-Control": "no-cache", 							"Arr-Disable-Session-Affinity": "true" 						}, 						"body": { 							"Error": "InvalidArgumentException", 							"Message": "Missing field field_a" 						} 					}, 					"user_id": "mndug437f43", 					"session_token": "23jdf0owekfmcn4u3qypxg09w4d8ayrcdx8nu2ng]s98y18cx98q3yhwmnhcfx43f" 					 }, { 					"request": { 						"time": "2016-09-09T04:50:42.914", 						"uri": "https://api.acmeinc.com/items/reviews/", 						"verb": "PATCH", 						"api_version": "1.1.0", 						"ip_address": "61.48.220.123", 						"headers": { 							"Host": "api.acmeinc.com", 							"Accept": "*/*", 							"Connection": "Keep-Alive", 							"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.0.2; C6906 Build/14.5.A.0.242)", 							"Content-Type": "application/json", 							"Content-Length": "126", 							"Accept-Encoding": "gzip" 						}, 						"body": { 							"items": [ 								{ 									"direction_type": 1, 									"discovery_id": "fwfrf", 									"liked": false 								}, 								{ 									"direction_type": 2, 									"discovery_id": "d43d3f", 									"liked": true 								} 							] 						} 					}, 					"response": { 						"time": "2016-09-09T04:50:42.914", 						"status": 500, 						"headers": { 							"Date": "Tue, 23 Aug 2016 23:46:49 GMT", 							"Vary": "Accept-Encoding", 							"Pragma": "no-cache", 							"Expires": "-1", 							"Content-Type": "application/json; charset=utf-8", 							"X-Powered-By": "ARR/3.0", 							"Cache-Control": "no-cache", 							"Arr-Disable-Session-Affinity": "true" 						}, 						"body": { 							"Error": "InvalidArgumentException", 							"Message": "Missing field field_a" 						} 					}, 					"user_id": "recvreedfef", 					"session_token": "xcvkrjmcfghwuignrmcmhxdhaaezse4w]s98y18cx98q3yhwmnhcfx43f" 					 } ]', EventModel.from_dictionary)

        # Perform the API call through the SDK function
        self.controller.create_events_batch(body)

        # Test response code
        self.assertEquals(self.response_catcher.response.status_code, 201)
