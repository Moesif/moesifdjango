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
        self.user_gov_rule = {
            "_id": "642f4fcea6ca1c38705d660d",
            "created_at": "2023-04-06T23:03:42.130",
            "org_id": "125:14",
            "app_id": "768:64",
            "name": "Gov new schema test",
            "block": True,
            "type": "user",
            "applied_to": "matching",
            "applied_to_unidentified": False,
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
                    "msg": "Blocked by Gov Rule",
                    "user_id": "{{0}}"
                }
            }
        }

        self.new_schema_regex_gov_rule = {
            "_id": "6439b3f5d5762a04c0623d8b",
            "regex_config": [
                {
                    "conditions": [
                        {
                            "path": "request.route",
                            "value": ".*555.*"
                        }
                    ]
                }
            ],
            "org_id": "125:14",
            "response": {
                "headers": {},
                "body": "eyJlcnJvciI6ImJsb2NrZWQgYnkgcmVnZXggcnVsZSBuZXcgc2NoZW1hIFtERVYgMTI1OjE0LTc2ODo2NF0ifQ==",
                "status": 303
            },
            "name": "Allow list test regex rule",
            "applied_to_unidentified": False,
            "created_at": "2023-04-14T20:13:41.478",
            "applied_to": "matching",
            "block": True,
            "state": 1,
            "type": "regex",
            "app_id": "768:64"
        }

        self.request_mapping_for_regex_config = \
            {
                'request.verb': 'GET',
                'request.route': 'http://127.0.0.1:8000/users/',
                'request.ip_address': '127.0.0.1',
                'response.status': 200
            }

        self.request_mapping_for_regex_config2 = \
            {
                'request.verb': 'GET',
                'request.route': 'http://127.0.0.1:8000/555/',
                'request.ip_address': '127.0.0.1',
                'response.status': 200
            }

        self.ready_for_body_request = True

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
        self.response = EventResponseModel(
            body='CgoKCjwhRE9DVFlQRSBodG1sPgo8aHRtbD4KICA8aGVhZD4KICAgIAoKICAgICAgCiAgICAgICAgPG1ldGEgaHR0cC1lcXVpdj0iQ29udGVudC1UeXBlIiBjb250ZW50PSJ0ZXh0L2h0bWw7IGNoYXJzZXQ9dXRmLTgiLz4KICAgICAgICA8bWV0YSBuYW1lPSJyb2JvdHMiIGNvbnRlbnQ9Ik5PTkUsTk9BUkNISVZFIiAvPgogICAgICAKCiAgICAgIDx0aXRsZT5Vc2VyIExpc3Qg4oCTIERqYW5nbyBSRVNUIGZyYW1ld29yazwvdGl0bGU+CgogICAgICAKICAgICAgICAKICAgICAgICAgIDxsaW5rIHJlbD0ic3R5bGVzaGVldCIgdHlwZT0idGV4dC9jc3MiIGhyZWY9Ii9zdGF0aWMvcmVzdF9mcmFtZXdvcmsvY3NzL2Jvb3RzdHJhcC5taW4uY3NzIi8+CiAgICAgICAgICA8bGluayByZWw9InN0eWxlc2hlZXQiIHR5cGU9InRleHQvY3NzIiBocmVmPSIvc3RhdGljL3Jlc3RfZnJhbWV3b3JrL2Nzcy9ib290c3RyYXAtdHdlYWtzLmNzcyIvPgogICAgICAgIAoKICAgICAgICA8bGluayByZWw9InN0eWxlc2hlZXQiIHR5cGU9InRleHQvY3NzIiBocmVmPSIvc3RhdGljL3Jlc3RfZnJhbWV3b3JrL2Nzcy9wcmV0dGlmeS5jc3MiLz4KICAgICAgICA8bGluayByZWw9InN0eWxlc2hlZXQiIHR5cGU9InRleHQvY3NzIiBocmVmPSIvc3RhdGljL3Jlc3RfZnJhbWV3b3JrL2Nzcy9kZWZhdWx0LmNzcyIvPgogICAgICAgIAogICAgICAKCiAgICAKICA8L2hlYWQ+CgogIAogIDxib2R5IGNsYXNzPSIiPgoKICAgIDxkaXYgY2xhc3M9IndyYXBwZXIiPgogICAgICAKICAgICAgICA8ZGl2IGNsYXNzPSJuYXZiYXIgbmF2YmFyLXN0YXRpYy10b3AgbmF2YmFyLWludmVyc2UiCiAgICAgICAgICAgICByb2xlPSJuYXZpZ2F0aW9uIiBhcmlhLWxhYmVsPSJuYXZiYXIiPgogICAgICAgICAgPGRpdiBjbGFzcz0iY29udGFpbmVyIj4KICAgICAgICAgICAgPHNwYW4+CiAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICA8YSBjbGFzcz0nbmF2YmFyLWJyYW5kJyByZWw9Im5vZm9sbG93IiBocmVmPSdodHRwczovL3d3dy5kamFuZ28tcmVzdC1mcmFtZXdvcmsub3JnLyc+CiAgICAgICAgICAgICAgICAgICAgRGphbmdvIFJFU1QgZnJhbWV3b3JrCiAgICAgICAgICAgICAgICA8L2E+CiAgICAgICAgICAgICAgCiAgICAgICAgICAgIDwvc3Bhbj4KICAgICAgICAgICAgPHVsIGNsYXNzPSJuYXYgbmF2YmFyLW5hdiBwdWxsLXJpZ2h0Ij4KICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICA8bGk+PGEgaHJlZj0nL2FwaS1hdXRoL2xvZ2luLz9uZXh0PS91c2Vycy8nPkxvZyBpbjwvYT48L2xpPgogICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgCiAgICAgICAgICAgIDwvdWw+CiAgICAgICAgICA8L2Rpdj4KICAgICAgICA8L2Rpdj4KICAgICAgCgogICAgICA8ZGl2IGNsYXNzPSJjb250YWluZXIiPgogICAgICAgIAogICAgICAgICAgPHVsIGNsYXNzPSJicmVhZGNydW1iIj4KICAgICAgICAgICAgCiAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICA8bGk+PGEgaHJlZj0iLyI+QXBpIFJvb3Q8L2E+PC9saT4KICAgICAgICAgICAgICAKICAgICAgICAgICAgCiAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICA8bGkgY2xhc3M9ImFjdGl2ZSI+PGEgaHJlZj0iL3VzZXJzLyI+VXNlciBMaXN0PC9hPjwvbGk+CiAgICAgICAgICAgICAgCiAgICAgICAgICAgIAogICAgICAgICAgPC91bD4KICAgICAgICAKCiAgICAgICAgPCEtLSBDb250ZW50IC0tPgogICAgICAgIDxkaXYgaWQ9ImNvbnRlbnQiIHJvbGU9Im1haW4iIGFyaWEtbGFiZWw9ImNvbnRlbnQiPgogICAgICAgICAgCgogICAgICAgICAgPGRpdiBjbGFzcz0icmVnaW9uIiAgYXJpYS1sYWJlbD0icmVxdWVzdCBmb3JtIj4KICAgICAgICAgIAoKICAgICAgICAgIAogICAgICAgICAgICA8Zm9ybSBpZD0iZ2V0LWZvcm0iIGNsYXNzPSJwdWxsLXJpZ2h0Ij4KICAgICAgICAgICAgICA8ZmllbGRzZXQ+CiAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgPGRpdiBjbGFzcz0iYnRuLWdyb3VwIGZvcm1hdC1zZWxlY3Rpb24iPgogICAgICAgICAgICAgICAgICAgIDxhIGNsYXNzPSJidG4gYnRuLXByaW1hcnkganMtdG9vbHRpcCIgaHJlZj0iL3VzZXJzLyIgcmVsPSJub2ZvbGxvdyIgdGl0bGU9Ik1ha2UgYSBHRVQgcmVxdWVzdCBvbiB0aGUgVXNlciBMaXN0IHJlc291cmNlIj5HRVQ8L2E+CgogICAgICAgICAgICAgICAgICAgIDxidXR0b24gY2xhc3M9ImJ0biBidG4tcHJpbWFyeSBkcm9wZG93bi10b2dnbGUganMtdG9vbHRpcCIgZGF0YS10b2dnbGU9ImRyb3Bkb3duIiB0aXRsZT0iU3BlY2lmeSBhIGZvcm1hdCBmb3IgdGhlIEdFVCByZXF1ZXN0Ij4KICAgICAgICAgICAgICAgICAgICAgIDxzcGFuIGNsYXNzPSJjYXJldCI+PC9zcGFuPgogICAgICAgICAgICAgICAgICAgIDwvYnV0dG9uPgogICAgICAgICAgICAgICAgICAgIDx1bCBjbGFzcz0iZHJvcGRvd24tbWVudSI+CiAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgPGxpPgogICAgICAgICAgICAgICAgICAgICAgICAgIDxhIGNsYXNzPSJqcy10b29sdGlwIGZvcm1hdC1vcHRpb24iIGhyZWY9Ii91c2Vycy8/Zm9ybWF0PWpzb24iIHJlbD0ibm9mb2xsb3ciIHRpdGxlPSJNYWtlIGEgR0VUIHJlcXVlc3Qgb24gdGhlIFVzZXIgTGlzdCByZXNvdXJjZSB3aXRoIHRoZSBmb3JtYXQgc2V0IHRvIGBqc29uYCI+anNvbjwvYT4KICAgICAgICAgICAgICAgICAgICAgICAgPC9saT4KICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICA8bGk+CiAgICAgICAgICAgICAgICAgICAgICAgICAgPGEgY2xhc3M9ImpzLXRvb2x0aXAgZm9ybWF0LW9wdGlvbiIgaHJlZj0iL3VzZXJzLz9mb3JtYXQ9YXBpIiByZWw9Im5vZm9sbG93IiB0aXRsZT0iTWFrZSBhIEdFVCByZXF1ZXN0IG9uIHRoZSBVc2VyIExpc3QgcmVzb3VyY2Ugd2l0aCB0aGUgZm9ybWF0IHNldCB0byBgYXBpYCI+YXBpPC9hPgogICAgICAgICAgICAgICAgICAgICAgICA8L2xpPgogICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgPC91bD4KICAgICAgICAgICAgICAgICAgPC9kaXY+CiAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICA8L2ZpZWxkc2V0PgogICAgICAgICAgICA8L2Zvcm0+CiAgICAgICAgICAKCiAgICAgICAgICAKICAgICAgICAgICAgPGZvcm0gY2xhc3M9ImJ1dHRvbi1mb3JtIiBhY3Rpb249Ii91c2Vycy8iIGRhdGEtbWV0aG9kPSJPUFRJT05TIj4KICAgICAgICAgICAgICA8YnV0dG9uIGNsYXNzPSJidG4gYnRuLXByaW1hcnkganMtdG9vbHRpcCIgdGl0bGU9Ik1ha2UgYW4gT1BUSU9OUyByZXF1ZXN0IG9uIHRoZSBVc2VyIExpc3QgcmVzb3VyY2UiPk9QVElPTlM8L2J1dHRvbj4KICAgICAgICAgICAgPC9mb3JtPgogICAgICAgICAgCgogICAgICAgICAgCgogICAgICAgICAgCgogICAgICAgICAgCgogICAgICAgICAgCiAgICAgICAgICA8L2Rpdj4KCiAgICAgICAgICAgIDxkaXYgY2xhc3M9ImNvbnRlbnQtbWFpbiIgcm9sZT0ibWFpbiIgIGFyaWEtbGFiZWw9Im1haW4gY29udGVudCI+CiAgICAgICAgICAgICAgPGRpdiBjbGFzcz0icGFnZS1oZWFkZXIiPgogICAgICAgICAgICAgICAgPGgxPlVzZXIgTGlzdDwvaDE+CiAgICAgICAgICAgICAgPC9kaXY+CiAgICAgICAgICAgICAgPGRpdiBzdHlsZT0iZmxvYXQ6bGVmdCI+CiAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgPHA+QVBJIGVuZHBvaW50IHRoYXQgYWxsb3dzIHVzZXJzIHRvIGJlIHZpZXdlZCBvciBlZGl0ZWQuPC9wPgogICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgPC9kaXY+CgogICAgICAgICAgICAgIAoKICAgICAgICAgICAgICA8ZGl2IGNsYXNzPSJyZXF1ZXN0LWluZm8iIHN0eWxlPSJjbGVhcjogYm90aCIgYXJpYS1sYWJlbD0icmVxdWVzdCBpbmZvIj4KICAgICAgICAgICAgICAgIDxwcmUgY2xhc3M9InByZXR0eXByaW50Ij48Yj5HRVQ8L2I+IC91c2Vycy88L3ByZT4KICAgICAgICAgICAgICA8L2Rpdj4KCiAgICAgICAgICAgICAgPGRpdiBjbGFzcz0icmVzcG9uc2UtaW5mbyIgYXJpYS1sYWJlbD0icmVzcG9uc2UgaW5mbyI+CiAgICAgICAgICAgICAgICA8cHJlIGNsYXNzPSJwcmV0dHlwcmludCI+PHNwYW4gY2xhc3M9Im1ldGEgbm9jb2RlIj48Yj5IVFRQIDIwMCBPSzwvYj4KPGI+QWxsb3c6PC9iPiA8c3BhbiBjbGFzcz0ibGl0Ij5HRVQsIFBPU1QsIEhFQUQsIE9QVElPTlM8L3NwYW4+CjxiPkNvbnRlbnQtVHlwZTo8L2I+IDxzcGFuIGNsYXNzPSJsaXQiPmFwcGxpY2F0aW9uL2pzb248L3NwYW4+CjxiPlZhcnk6PC9iPiA8c3BhbiBjbGFzcz0ibGl0Ij5BY2NlcHQ8L3NwYW4+Cgo8L3NwYW4+WwogICAgewogICAgICAgICZxdW90O3VybCZxdW90OzogJnF1b3Q7PGEgaHJlZj0iaHR0cDovLzEyNy4wLjAuMTo4MDAwL3VzZXJzLzcvIiByZWw9Im5vZm9sbG93Ij5odHRwOi8vMTI3LjAuMC4xOjgwMDAvdXNlcnMvNy88L2E+JnF1b3Q7LAogICAgICAgICZxdW90O3VzZXJuYW1lJnF1b3Q7OiAmcXVvdDt1c2VyNTcmcXVvdDssCiAgICAgICAgJnF1b3Q7ZW1haWwmcXVvdDs6ICZxdW90OyZxdW90OywKICAgICAgICAmcXVvdDtncm91cHMmcXVvdDs6IFtdCiAgICB9LAogICAgewogICAgICAgICZxdW90O3VybCZxdW90OzogJnF1b3Q7PGEgaHJlZj0iaHR0cDovLzEyNy4wLjAuMTo4MDAwL3VzZXJzLzYvIiByZWw9Im5vZm9sbG93Ij5odHRwOi8vMTI3LjAuMC4xOjgwMDAvdXNlcnMvNi88L2E+JnF1b3Q7LAogICAgICAgICZxdW90O3VzZXJuYW1lJnF1b3Q7OiAmcXVvdDt1c2VyNTYmcXVvdDssCiAgICAgICAgJnF1b3Q7ZW1haWwmcXVvdDs6ICZxdW90OyZxdW90OywKICAgICAgICAmcXVvdDtncm91cHMmcXVvdDs6IFtdCiAgICB9LAogICAgewogICAgICAgICZxdW90O3VybCZxdW90OzogJnF1b3Q7PGEgaHJlZj0iaHR0cDovLzEyNy4wLjAuMTo4MDAwL3VzZXJzLzUvIiByZWw9Im5vZm9sbG93Ij5odHRwOi8vMTI3LjAuMC4xOjgwMDAvdXNlcnMvNS88L2E+JnF1b3Q7LAogICAgICAgICZxdW90O3VzZXJuYW1lJnF1b3Q7OiAmcXVvdDt1c2VyNTUmcXVvdDssCiAgICAgICAgJnF1b3Q7ZW1haWwmcXVvdDs6ICZxdW90OyZxdW90OywKICAgICAgICAmcXVvdDtncm91cHMmcXVvdDs6IFtdCiAgICB9LAogICAgewogICAgICAgICZxdW90O3VybCZxdW90OzogJnF1b3Q7PGEgaHJlZj0iaHR0cDovLzEyNy4wLjAuMTo4MDAwL3VzZXJzLzQvIiByZWw9Im5vZm9sbG93Ij5odHRwOi8vMTI3LjAuMC4xOjgwMDAvdXNlcnMvNC88L2E+JnF1b3Q7LAogICAgICAgICZxdW90O3VzZXJuYW1lJnF1b3Q7OiAmcXVvdDt1c2VyNTQmcXVvdDssCiAgICAgICAgJnF1b3Q7ZW1haWwmcXVvdDs6ICZxdW90OyZxdW90OywKICAgICAgICAmcXVvdDtncm91cHMmcXVvdDs6IFtdCiAgICB9LAogICAgewogICAgICAgICZxdW90O3VybCZxdW90OzogJnF1b3Q7PGEgaHJlZj0iaHR0cDovLzEyNy4wLjAuMTo4MDAwL3VzZXJzLzMvIiByZWw9Im5vZm9sbG93Ij5odHRwOi8vMTI3LjAuMC4xOjgwMDAvdXNlcnMvMy88L2E+JnF1b3Q7LAogICAgICAgICZxdW90O3VzZXJuYW1lJnF1b3Q7OiAmcXVvdDt1c2VyNTMmcXVvdDssCiAgICAgICAgJnF1b3Q7ZW1haWwmcXVvdDs6ICZxdW90OyZxdW90OywKICAgICAgICAmcXVvdDtncm91cHMmcXVvdDs6IFtdCiAgICB9LAogICAgewogICAgICAgICZxdW90O3VybCZxdW90OzogJnF1b3Q7PGEgaHJlZj0iaHR0cDovLzEyNy4wLjAuMTo4MDAwL3VzZXJzLzIvIiByZWw9Im5vZm9sbG93Ij5odHRwOi8vMTI3LjAuMC4xOjgwMDAvdXNlcnMvMi88L2E+JnF1b3Q7LAogICAgICAgICZxdW90O3VzZXJuYW1lJnF1b3Q7OiAmcXVvdDt1c2VyNTEmcXVvdDssCiAgICAgICAgJnF1b3Q7ZW1haWwmcXVvdDs6ICZxdW90OyZxdW90OywKICAgICAgICAmcXVvdDtncm91cHMmcXVvdDs6IFsKICAgICAgICAgICAgJnF1b3Q7PGEgaHJlZj0iaHR0cDovLzEyNy4wLjAuMTo4MDAwL2dyb3Vwcy8xLyIgcmVsPSJub2ZvbGxvdyI+aHR0cDovLzEyNy4wLjAuMTo4MDAwL2dyb3Vwcy8xLzwvYT4mcXVvdDsKICAgICAgICBdCiAgICB9LAogICAgewogICAgICAgICZxdW90O3VybCZxdW90OzogJnF1b3Q7PGEgaHJlZj0iaHR0cDovLzEyNy4wLjAuMTo4MDAwL3VzZXJzLzEvIiByZWw9Im5vZm9sbG93Ij5odHRwOi8vMTI3LjAuMC4xOjgwMDAvdXNlcnMvMS88L2E+JnF1b3Q7LAogICAgICAgICZxdW90O3VzZXJuYW1lJnF1b3Q7OiAmcXVvdDt1c2VyNTAmcXVvdDssCiAgICAgICAgJnF1b3Q7ZW1haWwmcXVvdDs6ICZxdW90OyZxdW90OywKICAgICAgICAmcXVvdDtncm91cHMmcXVvdDs6IFsKICAgICAgICAgICAgJnF1b3Q7PGEgaHJlZj0iaHR0cDovLzEyNy4wLjAuMTo4MDAwL2dyb3Vwcy8xLyIgcmVsPSJub2ZvbGxvdyI+aHR0cDovLzEyNy4wLjAuMTo4MDAwL2dyb3Vwcy8xLzwvYT4mcXVvdDsKICAgICAgICBdCiAgICB9Cl08L3ByZT4KICAgICAgICAgICAgICA8L2Rpdj4KICAgICAgICAgICAgPC9kaXY+CgogICAgICAgICAgICAKICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgIDxkaXYgY2xhc3M9InRhYmJhYmxlIj4KICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgPHVsIGNsYXNzPSJuYXYgbmF2LXRhYnMgZm9ybS1zd2l0Y2hlciI+CiAgICAgICAgICAgICAgICAgICAgICA8bGk+CiAgICAgICAgICAgICAgICAgICAgICAgIDxhIG5hbWU9J2h0bWwtdGFiJyBocmVmPSIjcG9zdC1vYmplY3QtZm9ybSIgZGF0YS10b2dnbGU9InRhYiI+SFRNTCBmb3JtPC9hPgogICAgICAgICAgICAgICAgICAgICAgPC9saT4KICAgICAgICAgICAgICAgICAgICAgIDxsaT4KICAgICAgICAgICAgICAgICAgICAgICAgPGEgbmFtZT0ncmF3LXRhYicgaHJlZj0iI3Bvc3QtZ2VuZXJpYy1jb250ZW50LWZvcm0iIGRhdGEtdG9nZ2xlPSJ0YWIiPlJhdyBkYXRhPC9hPgogICAgICAgICAgICAgICAgICAgICAgPC9saT4KICAgICAgICAgICAgICAgICAgICA8L3VsPgogICAgICAgICAgICAgICAgICAKCiAgICAgICAgICAgICAgICAgIDxkaXYgY2xhc3M9IndlbGwgdGFiLWNvbnRlbnQiPgogICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgPGRpdiBjbGFzcz0idGFiLXBhbmUiIGlkPSJwb3N0LW9iamVjdC1mb3JtIj4KICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgPGZvcm0gYWN0aW9uPSIvdXNlcnMvIiBtZXRob2Q9IlBPU1QiIGVuY3R5cGU9Im11bHRpcGFydC9mb3JtLWRhdGEiIGNsYXNzPSJmb3JtLWhvcml6b250YWwiIG5vdmFsaWRhdGU+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICA8ZmllbGRzZXQ+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIDxpbnB1dCB0eXBlPSJoaWRkZW4iIG5hbWU9ImNzcmZtaWRkbGV3YXJldG9rZW4iIHZhbHVlPSJHTzJLT2k4QmdwdmxqNXVLZEw3Tjc2eEJNQXhWZGZqM3VQVkhlQlI4RWpWN3hCWUM5RTlkWnFXclk5TmV5SmcyIj4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCgogIAoKICAKICAgIDxkaXYgY2xhc3M9ImZvcm0tZ3JvdXAgIj4KICAKICAgIDxsYWJlbCBjbGFzcz0iY29sLXNtLTIgY29udHJvbC1sYWJlbCAiPgogICAgICBVc2VybmFtZQogICAgPC9sYWJlbD4KICAKCiAgPGRpdiBjbGFzcz0iY29sLXNtLTEwIj4KICAgIDxpbnB1dCBuYW1lPSJ1c2VybmFtZSIgY2xhc3M9ImZvcm0tY29udHJvbCIgdHlwZT0idGV4dCIgIHZhbHVlPSIiID4KCiAgICAKCiAgICAKICAgICAgPHNwYW4gY2xhc3M9ImhlbHAtYmxvY2siPlJlcXVpcmVkLiAxNTAgY2hhcmFjdGVycyBvciBmZXdlci4gTGV0dGVycywgZGlnaXRzIGFuZCBALy4vKy8tL18gb25seS48L3NwYW4+CiAgICAKICA8L2Rpdj4KPC9kaXY+CgogIAoKICAKICAgIDxkaXYgY2xhc3M9ImZvcm0tZ3JvdXAgIj4KICAKICAgIDxsYWJlbCBjbGFzcz0iY29sLXNtLTIgY29udHJvbC1sYWJlbCAiPgogICAgICBFbWFpbCBhZGRyZXNzCiAgICA8L2xhYmVsPgogIAoKICA8ZGl2IGNsYXNzPSJjb2wtc20tMTAiPgogICAgPGlucHV0IG5hbWU9ImVtYWlsIiBjbGFzcz0iZm9ybS1jb250cm9sIiB0eXBlPSJlbWFpbCIgIHZhbHVlPSIiID4KCiAgICAKCiAgICAKICA8L2Rpdj4KPC9kaXY+CgogIAoKICAKICAgIAoKCgoKPGRpdiBjbGFzcz0iZm9ybS1ncm91cCI+CiAgCiAgICA8bGFiZWwgY2xhc3M9ImNvbC1zbS0yIGNvbnRyb2wtbGFiZWwgIj4KICAgICAgR3JvdXBzCiAgICA8L2xhYmVsPgogIAoKICA8ZGl2IGNsYXNzPSJjb2wtc20tMTAiPgogICAgPHNlbGVjdCBtdWx0aXBsZSAgY2xhc3M9ImZvcm0tY29udHJvbCIgbmFtZT0iZ3JvdXBzIj4KICAgICAgCiAgICAgICAgCiAgICAgICAgICA8b3B0aW9uIHZhbHVlPSJodHRwOi8vMTI3LjAuMC4xOjgwMDAvZ3JvdXBzLzEvIiAgPmE8L29wdGlvbj4KICAgICAgICAKICAgICAgCiAgICAgICAgCiAgICAgICAgICA8b3B0aW9uIHZhbHVlPSJodHRwOi8vMTI3LjAuMC4xOjgwMDAvZ3JvdXBzLzIvIiAgPmdyb3VwIDE8L29wdGlvbj4KICAgICAgICAKICAgICAgCiAgICA8L3NlbGVjdD4KCiAgICAKCiAgICAKICAgICAgPHNwYW4gY2xhc3M9ImhlbHAtYmxvY2siPlRoZSBncm91cHMgdGhpcyB1c2VyIGJlbG9uZ3MgdG8uIEEgdXNlciB3aWxsIGdldCBhbGwgcGVybWlzc2lvbnMgZ3JhbnRlZCB0byBlYWNoIG9mIHRoZWlyIGdyb3Vwcy48L3NwYW4+CiAgICAKICA8L2Rpdj4KPC9kaXY+CgogIAoKCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIDxkaXYgY2xhc3M9ImZvcm0tYWN0aW9ucyI+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgPGJ1dHRvbiBjbGFzcz0iYnRuIGJ0bi1wcmltYXJ5IGpzLXRvb2x0aXAiIHRpdGxlPSJNYWtlIGEgUE9TVCByZXF1ZXN0IG9uIHRoZSBVc2VyIExpc3QgcmVzb3VyY2UiPlBPU1Q8L2J1dHRvbj4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgPC9kaXY+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICA8L2ZpZWxkc2V0PgogICAgICAgICAgICAgICAgICAgICAgICAgIDwvZm9ybT4KICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICA8L2Rpdj4KICAgICAgICAgICAgICAgICAgICAKCiAgICAgICAgICAgICAgICAgICAgPGRpdiBjbGFzcz0idGFiLXBhbmUiIGlkPSJwb3N0LWdlbmVyaWMtY29udGVudC1mb3JtIj4KICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICA8Zm9ybSBhY3Rpb249Ii91c2Vycy8iIG1ldGhvZD0iUE9TVCIgY2xhc3M9ImZvcm0taG9yaXpvbnRhbCI+CiAgICAgICAgICAgICAgICAgICAgICAgICAgPGZpZWxkc2V0PgogICAgICAgICAgICAgICAgICAgICAgICAgICAgCgoKICA8ZGl2IGNsYXNzPSJmb3JtLWdyb3VwIj4KICAgIDxsYWJlbCBmb3I9ImlkX19jb250ZW50X3R5cGUiIGNsYXNzPSJjb2wtc20tMiBjb250cm9sLWxhYmVsIj5NZWRpYSB0eXBlOjwvbGFiZWw+CiAgICA8ZGl2IGNsYXNzPSJjb2wtc20tMTAiPgogICAgICA8c2VsZWN0IG5hbWU9Il9jb250ZW50X3R5cGUiIGRhdGEtb3ZlcnJpZGU9ImNvbnRlbnQtdHlwZSIgaWQ9ImlkX19jb250ZW50X3R5cGUiIGNsYXNzPSJmb3JtLWNvbnRyb2wiPgogIDxvcHRpb24gdmFsdWU9ImFwcGxpY2F0aW9uL2pzb24iIHNlbGVjdGVkPmFwcGxpY2F0aW9uL2pzb248L29wdGlvbj4KCiAgPG9wdGlvbiB2YWx1ZT0iYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkIj5hcHBsaWNhdGlvbi94LXd3dy1mb3JtLXVybGVuY29kZWQ8L29wdGlvbj4KCiAgPG9wdGlvbiB2YWx1ZT0ibXVsdGlwYXJ0L2Zvcm0tZGF0YSI+bXVsdGlwYXJ0L2Zvcm0tZGF0YTwvb3B0aW9uPgoKPC9zZWxlY3Q+CiAgICAgIDxzcGFuIGNsYXNzPSJoZWxwLWJsb2NrIj48L3NwYW4+CiAgICA8L2Rpdj4KICA8L2Rpdj4KCiAgPGRpdiBjbGFzcz0iZm9ybS1ncm91cCI+CiAgICA8bGFiZWwgZm9yPSJpZF9fY29udGVudCIgY2xhc3M9ImNvbC1zbS0yIGNvbnRyb2wtbGFiZWwiPkNvbnRlbnQ6PC9sYWJlbD4KICAgIDxkaXYgY2xhc3M9ImNvbC1zbS0xMCI+CiAgICAgIDx0ZXh0YXJlYSBuYW1lPSJfY29udGVudCIgY29scz0iNDAiIHJvd3M9IjEwIiBkYXRhLW92ZXJyaWRlPSJjb250ZW50IiBpZD0iaWRfX2NvbnRlbnQiIGNsYXNzPSJmb3JtLWNvbnRyb2wiPgp7CiAgICAmcXVvdDt1c2VybmFtZSZxdW90OzogJnF1b3Q7JnF1b3Q7LAogICAgJnF1b3Q7ZW1haWwmcXVvdDs6ICZxdW90OyZxdW90OywKICAgICZxdW90O2dyb3VwcyZxdW90OzogW10KfTwvdGV4dGFyZWE+CiAgICAgIDxzcGFuIGNsYXNzPSJoZWxwLWJsb2NrIj48L3NwYW4+CiAgICA8L2Rpdj4KICA8L2Rpdj4KCgogICAgICAgICAgICAgICAgICAgICAgICAgICAgPGRpdiBjbGFzcz0iZm9ybS1hY3Rpb25zIj4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgPGJ1dHRvbiBjbGFzcz0iYnRuIGJ0bi1wcmltYXJ5IGpzLXRvb2x0aXAiIHRpdGxlPSJNYWtlIGEgUE9TVCByZXF1ZXN0IG9uIHRoZSBVc2VyIExpc3QgcmVzb3VyY2UiPlBPU1Q8L2J1dHRvbj4KICAgICAgICAgICAgICAgICAgICAgICAgICAgIDwvZGl2PgogICAgICAgICAgICAgICAgICAgICAgICAgIDwvZmllbGRzZXQ+CiAgICAgICAgICAgICAgICAgICAgICAgIDwvZm9ybT4KICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgIDwvZGl2PgogICAgICAgICAgICAgICAgICA8L2Rpdj4KICAgICAgICAgICAgICAgIDwvZGl2PgogICAgICAgICAgICAgIAoKICAgICAgICAgICAgICAKICAgICAgICAgICAgCiAgICAgICAgICAKICAgICAgICA8L2Rpdj48IS0tIC8uY29udGVudCAtLT4KICAgICAgPC9kaXY+PCEtLSAvLmNvbnRhaW5lciAtLT4KICAgIDwvZGl2PjwhLS0gLi93cmFwcGVyIC0tPgoKICAgIAoKICAgIAogICAgICA8c2NyaXB0PgogICAgICAgIHdpbmRvdy5kcmYgPSB7CiAgICAgICAgICBjc3JmSGVhZGVyTmFtZTogIlgtQ1NSRlRPS0VOIiwKICAgICAgICAgIGNzcmZUb2tlbjogIkdPMktPaThCZ3B2bGo1dUtkTDdONzZ4Qk1BeFZkZmozdVBWSGVCUjhFalY3eEJZQzlFOWRacVdyWTlOZXlKZzIiCiAgICAgICAgfTsKICAgICAgPC9zY3JpcHQ+CiAgICAgIDxzY3JpcHQgc3JjPSIvc3RhdGljL3Jlc3RfZnJhbWV3b3JrL2pzL2pxdWVyeS0zLjUuMS5taW4uanMiPjwvc2NyaXB0PgogICAgICA8c2NyaXB0IHNyYz0iL3N0YXRpYy9yZXN0X2ZyYW1ld29yay9qcy9hamF4LWZvcm0uanMiPjwvc2NyaXB0PgogICAgICA8c2NyaXB0IHNyYz0iL3N0YXRpYy9yZXN0X2ZyYW1ld29yay9qcy9jc3JmLmpzIj48L3NjcmlwdD4KICAgICAgPHNjcmlwdCBzcmM9Ii9zdGF0aWMvcmVzdF9mcmFtZXdvcmsvanMvYm9vdHN0cmFwLm1pbi5qcyI+PC9zY3JpcHQ+CiAgICAgIDxzY3JpcHQgc3JjPSIvc3RhdGljL3Jlc3RfZnJhbWV3b3JrL2pzL3ByZXR0aWZ5LW1pbi5qcyI+PC9zY3JpcHQ+CiAgICAgIDxzY3JpcHQgc3JjPSIvc3RhdGljL3Jlc3RfZnJhbWV3b3JrL2pzL2RlZmF1bHQuanMiPjwvc2NyaXB0PgogICAgICA8c2NyaXB0PgogICAgICAgICQoZG9jdW1lbnQpLnJlYWR5KGZ1bmN0aW9uKCkgewogICAgICAgICAgJCgnZm9ybScpLmFqYXhGb3JtKCk7CiAgICAgICAgfSk7CiAgICAgIDwvc2NyaXB0PgogICAgCgogIDwvYm9keT4KICAKPC9odG1sPgo=',
            headers={'Content-Type': 'text/html; charset=utf-8', 'Vary': 'Accept', 'Allow': 'GET, POST, HEAD, OPTIONS',
                     'X-Frame-Options': 'DENY', 'x-moesif-transaction-id': '7fa3a0a9-a6a2-42a3-893f-037c339fa290'},
            status=200,
            time='2023-04-12T21:49:41.206',
            transfer_encoding='base64'
        )

        self.event = EventModel(
            user_id='u1',
            company_id='c1',
            direction='Incoming',
            metadata={'datacenter': 'westus', 'deployment_version': 'v1.2.3'},
            request=self.request,
            response=self.response,
            session_token='XXXXXXXXXX')

        self.user_entity_rules_from_config = {'user_rules':
            {
                'u1': [
                    {'rules': '642f4fcea6ca1c38705d660d', 'values': {'0': 'u1'}},
                    {'rules': '6435bc43682c9b013785e60f'},
                    {'rules': '643e13106bd6416306aa187c', 'values': {'0': 'u1', '1': 'c1'}}
                ]
            },
            'company_rules': {}
        }

    def test_get_entity_rule_mapping_from_config(self):
        rule_values = self.gov_helper.get_entity_rule_mapping_from_config(self.user_entity_rules_from_config, 'user_rules', 'u1')
        print(rule_values)


    def test_check_event_should_blocked_by_rule_should_block(self):
        block = self.gov_helper.check_event_should_blocked_by_rule(self.user_gov_rule,
                                                                   self.request_mapping_for_regex_config,
                                                                   self.ready_for_body_request)
        self.assertEqual(block, True)

    def test_check_event_should_blocked_by_rule_should_not_block(self):
        self.request_mapping_for_regex_config['request.route'] = 'http://127.0.0.1:8000/groups/'
        block = self.gov_helper.check_event_should_blocked_by_rule(self.user_gov_rule,
                                                                   self.request_mapping_for_regex_config,
                                                                   self.ready_for_body_request)
        self.assertEqual(block, False)

    def test_apply_governance_rules_regex_matching(self):
        self.new_schema_regex_gov_rule['applied_to'] = AppliedTo.MATCHING.value
        self.request.uri = 'http://127.0.0.1:8000/555/'
        self.event.request = self.request

        regex_gov_rules = {self.new_schema_regex_gov_rule.get('_id'): self.new_schema_regex_gov_rule}
        blocking_response = self.gov_helper.apply_governance_rules(
            self.event,
            None, None, None, None,
            None, None, None, None,
            regex_gov_rules,
            True
        )
        self.assertEqual(blocking_response.blocked, True)
        self.assertEqual(blocking_response.block_response_status, self.new_schema_regex_gov_rule['response']['status'])
        self.assertEqual(blocking_response.block_response_body, self.new_schema_regex_gov_rule['response']['body'])
        self.assertEqual(blocking_response.block_response_headers,
                         self.new_schema_regex_gov_rule['response']['headers'])

    def test_apply_governance_rules_regex_not_matching(self):
        self.new_schema_regex_gov_rule['applied_to'] = AppliedTo.NOT_MATCHING.value
        self.request.uri = 'http://127.0.0.1:8000/556/'  # the url not matching with regex rule config
        self.event.request = self.request

        regex_gov_rules = {self.new_schema_regex_gov_rule.get('_id'): self.new_schema_regex_gov_rule}
        blocking_response = self.gov_helper.apply_governance_rules(
            self.event,
            None, None, None, None,
            None, None, None, None,
            regex_gov_rules,
            True
        )
        self.assertEqual(blocking_response.blocked, True)
        self.assertEqual(blocking_response.block_response_status, self.new_schema_regex_gov_rule['response']['status'])
        self.assertEqual(blocking_response.block_response_body, self.new_schema_regex_gov_rule['response']['body'])
        self.assertEqual(blocking_response.block_response_headers,
                         self.new_schema_regex_gov_rule['response']['headers'])
        # self.assertIsNone(blocking_response)

    def test_apply_governance_rules_user_matching_identified(self):
        self.user_gov_rule['type'] = RuleType.USER.value
        self.user_gov_rule['applied_to'] = AppliedTo.MATCHING.value
        self.user_gov_rule['applied_to_unidentified'] = False
        identified_user_rules = {self.user_gov_rule.get('_id'): self.user_gov_rule}
        blocking_response = self.gov_helper.apply_governance_rules(
            self.event,
            self.event.user_id, None, None,
            self.user_entity_rules_from_config,
            identified_user_rules,
            None, None, None, None, True
        )

        self.assertEqual(blocking_response.blocked, True)
        self.assertEqual(self.user_gov_rule['response']['status'], blocking_response.block_response_status)
        self.assertEqual({'msg': 'Blocked by Gov Rule', 'user_id': '{}'.format(self.event.user_id)}, blocking_response.block_response_body)
        self.assertEqual(self.user_gov_rule['response']['headers'], blocking_response.block_response_headers)

    def test_apply_governance_rules_user_matching_unidentified(self):
        self.user_gov_rule['type'] = RuleType.USER.value
        self.user_gov_rule['applied_to'] = AppliedTo.MATCHING.value
        self.user_gov_rule['applied_to_unidentified'] = True
        unidentified_user_rules = {self.user_gov_rule.get('_id'): self.user_gov_rule}
        not_null_user_blocking_response = self.gov_helper.apply_governance_rules(
            self.event,
            self.event.user_id, None, None,
            self.user_entity_rules_from_config,
            None, unidentified_user_rules, None, None, None, True
        )
        self.assertEqual(not_null_user_blocking_response.blocked, True)
        self.assertEqual(self.user_gov_rule['response']['status'], not_null_user_blocking_response.block_response_status)
        self.assertEqual({'msg': 'Blocked by Gov Rule', 'user_id': '{}'.format(self.event.user_id)}, not_null_user_blocking_response.block_response_body)
        self.assertEqual(self.user_gov_rule['response']['headers'], not_null_user_blocking_response.block_response_headers)

        self.event.user_id = None
        null_user_blocking_response = self.gov_helper.apply_governance_rules(
            self.event,
            self.event.user_id, None, None,
            self.user_entity_rules_from_config,
            None,
            unidentified_user_rules,
            None, None, None, True
        )
        self.assertEqual(null_user_blocking_response.blocked, True)
        self.assertEqual(self.user_gov_rule['response']['status'], null_user_blocking_response.block_response_status)
        self.assertEqual(self.user_gov_rule['response']['body'], null_user_blocking_response.block_response_body)
        self.assertEqual(self.user_gov_rule['response']['headers'], null_user_blocking_response.block_response_headers)

    def test_apply_governance_rules_user_not_matching_identified(self):
        self.user_gov_rule['type'] = RuleType.USER.value
        self.user_gov_rule['applied_to'] = AppliedTo.NOT_MATCHING.value
        self.user_gov_rule['applied_to_unidentified'] = False

        identified_user_rules = {self.user_gov_rule.get('_id'): self.user_gov_rule}
        # not matched event: should block
        self.request.uri = 'http://127.0.0.1:8000/not_matching/'  # the url not matching with regex rule config
        self.event.request = self.request

        blocking_response = self.gov_helper.apply_governance_rules(
            self.event,
            self.event.user_id, None, None,
            self.user_entity_rules_from_config,
            identified_user_rules,
            None, None, None, None, True
        )

        self.assertEqual(blocking_response.blocked, True)
        self.assertEqual(self.user_gov_rule['response']['status'], blocking_response.block_response_status)
        self.assertEqual({'msg': 'Blocked by Gov Rule', 'user_id': '{}'.format(self.event.user_id)},
                         blocking_response.block_response_body)
        self.assertEqual(self.user_gov_rule['response']['headers'], blocking_response.block_response_headers)

        # matched event: should not block
        self.request.uri = 'http://127.0.0.1:8000/users/'  # the url not matching with regex rule config
        self.event.request = self.request

        blocking_response = self.gov_helper.apply_governance_rules(
            self.event,
            self.event.user_id, None, None,
            self.user_entity_rules_from_config,
            identified_user_rules,
            None, None, None, None, True
        )

        self.assertIsNone(blocking_response)

    def test_apply_governance_rules_user_not_matching_unidentified(self):
        self.user_gov_rule['type'] = RuleType.USER.value
        self.user_gov_rule['applied_to'] = AppliedTo.NOT_MATCHING.value
        self.user_gov_rule['applied_to_unidentified'] = True
        unidentified_user_rules = {self.user_gov_rule.get('_id'): self.user_gov_rule}

        # matched event: should not block
        self.request.uri = 'http://127.0.0.1:8000/users/'  # the url not matching with regex rule config
        self.event.request = self.request
        self.event.user_id = 'u1'
        not_null_user_blocking_response = self.gov_helper.apply_governance_rules(
            self.event,
            self.event.user_id, None, None,
            self.user_entity_rules_from_config,
            None, unidentified_user_rules, None, None, None, True
        )
        self.assertIsNone(not_null_user_blocking_response)

        self.event.user_id = None
        null_user_blocking_response = self.gov_helper.apply_governance_rules(
            self.event,
            self.event.user_id, None, None,
            self.user_entity_rules_from_config,
            None,
            unidentified_user_rules,
            None, None, None, True
        )
        self.assertIsNone(null_user_blocking_response)

        # not matched event: should block
        self.request.uri = 'http://127.0.0.1:8000/not_matching/'  # the url not matching with regex rule config
        self.event.request = self.request
        self.event.user_id = 'u1'
        not_null_user_blocking_response = self.gov_helper.apply_governance_rules(
            self.event,
            self.event.user_id, None, None,
            self.user_entity_rules_from_config,
            None, unidentified_user_rules, None, None, None, True
        )
        self.assertEqual(not_null_user_blocking_response.blocked, True)
        self.assertEqual(self.user_gov_rule['response']['status'],
                         not_null_user_blocking_response.block_response_status)
        self.assertEqual({'msg': 'Blocked by Gov Rule', 'user_id': '{}'.format(self.event.user_id)},
                         not_null_user_blocking_response.block_response_body)
        self.assertEqual(self.user_gov_rule['response']['headers'],
                         not_null_user_blocking_response.block_response_headers)

        self.event.user_id = None
        null_user_blocking_response = self.gov_helper.apply_governance_rules(
            self.event,
            self.event.user_id, None, None,
            self.user_entity_rules_from_config,
            None,
            unidentified_user_rules,
            None, None, None, True
        )
        self.assertEqual(null_user_blocking_response.blocked, True)
        self.assertEqual(self.user_gov_rule['response']['status'], null_user_blocking_response.block_response_status)
        self.assertEqual(self.user_gov_rule['response']['body'], null_user_blocking_response.block_response_body)
        self.assertEqual(self.user_gov_rule['response']['headers'], null_user_blocking_response.block_response_headers)


if __name__ == '__main__':
    unittest.main()
