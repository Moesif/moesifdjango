import unittest
from ..moesif_gov import *


class GovRulesTestCase(unittest.TestCase):
    def setUp(self):
        self.request = EventRequestModel(
            body="LS0tLS0tV2ViS2l0Rm9ybUJvdW5kYXJ5blNmSzhhVUUwRUYxSUdudw0KQ29udGVudC1EaXNwb3NpdGlvbjogZm9ybS1kYXRhOyBuYW1lPSJjc3JmbWlkZGxld2FyZXRva2VuIg0KDQp1WEs3Qm5sMTFOUHJKNGFlVWthbGU2eDZ0TXdPQnk1SWlZRDQxRzR5cEhmZFhBRTZRZGNMNnFXV0ZsTTdXMjJIDQotLS0tLS1XZWJLaXRGb3JtQm91bmRhcnluU2ZLOGFVRTBFRjFJR253DQpDb250ZW50LURpc3Bvc2l0aW9uOiBmb3JtLWRhdGE7IG5hbWU9InVzZXJuYW1lIg0KDQp1c2VyIDU5DQotLS0tLS1XZWJLaXRGb3JtQm91bmRhcnluU2ZLOGFVRTBFRjFJR253DQpDb250ZW50LURpc3Bvc2l0aW9uOiBmb3JtLWRhdGE7IG5hbWU9ImVtYWlsIg0KDQoNCi0tLS0tLVdlYktpdEZvcm1Cb3VuZGFyeW5TZks4YVVFMEVGMUlHbnctLQ0K",
            headers={'CONTENT-LENGTH': '408',
                     'CONTENT-TYPE': 'multipart/form-data; boundary=----WebKitFormBoundarynSfK8aUE0EF1IGnw',
                     'HOST': '127.0.0.1:8000', 'CONNECTION': 'keep-alive', 'CACHE-CONTROL': 'max-age=0',
                     'SEC-CH-UA': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
                     'SEC-CH-UA-MOBILE': '?0', 'SEC-CH-UA-PLATFORM': '"macOS"', 'UPGRADE-INSECURE-REQUESTS': '1',
                     'ORIGIN': 'http://127.0.0.1:8000',
                     'USER-AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
                     'ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                     'SEC-FETCH-SITE': 'same-origin', 'SEC-FETCH-MODE': 'navigate', 'SEC-FETCH-USER': '?1',
                     'SEC-FETCH-DEST': 'document', 'REFERER': 'http://127.0.0.1:8000/users/',
                     'ACCEPT-ENCODING': 'gzip, deflate, br', 'ACCEPT-LANGUAGE': 'en-US,en;q=0.9',
                     'COOKIE': 'csrftoken=Ys3hZTsC7OL7HacTyYvgAsaRbhXoPF7GMtWepcb9vIbTVGGLuRxGsMzHnQdHa94F',
                     'X-MOESIF-TRANSACTION-ID': 'd1965385-708f-485d-8370-b02ab334f6ef'},
            ip_address='127.0.0.1',
            time='2023-04-12T20:33:41.047',
            transfer_encoding='base64',
            uri='http://127.0.0.1:8000/users/',
            verb='POST'
        )
        self.gov_helper = MoesifGovRuleHelper()
        self.gov_rule = {
            "_id": "642f4fcea6ca1c38705d660d",
            "created_at": "2023-04-06T23:03:42.130",
            "org_id": "125:14",
            "app_id": "768:64",
            "name": "Gov new schema test",
            "block": True,
            "type": "user",
            "applied_to": "matching",
            "applied_to_unidentified": True,
            "variables": [
                {
                    "name": "0",
                    "path": "user_id"
                }
            ],
            "regex_config": [
                {
                    "conditions": [
                        {
                            "path": "request.route",
                            "value": ".*user.*"
                        }
                    ]
                },
                {
                    "conditions": [
                        {
                            "path": "request.route",
                            "value": ".*789.*"
                        }
                    ]
                }
            ],
            "response": {
                "status": 305,
                "headers": {},
                "body": {
                    "msg": "Blocked by Gov Rule on [DEV 125:14-768:64]",
                    "user_id": "{{0}}"
                }
            }
        }

        self.request_mapping_for_regex_config = \
            {
                'request.verb': 'GET',
                'request.route': 'http://127.0.0.1:8000/users/',
                'request.ip_address': '127.0.0.1',
                'response.status': 200
             }

        self.ready_for_body_request = True

    ob = MoesifGovRuleHelper()

    def test_something(self):
        print(self.request)
        self.assertEqual(True, True)  # add assertion here

    def test_check_event_should_blocked_by_rule_should_block(self):
        block = self.gov_helper.check_event_should_blocked_by_rule(self.gov_rule, self.request_mapping_for_regex_config, self.ready_for_body_request)
        self.assertEqual(block, True)

    def test_check_event_should_blocked_by_rule_should_not_block(self):
        self.request_mapping_for_regex_config['request.route'] = 'http://127.0.0.1:8000/groups/'
        block = self.gov_helper.check_event_should_blocked_by_rule(self.gov_rule, self.request_mapping_for_regex_config, self.ready_for_body_request)
        self.assertEqual(block, False)


if __name__ == '__main__':
    unittest.main()
