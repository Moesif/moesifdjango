import json
from moesifapi import APIException


class Governance_Rules_Cacher:

    def __init__(self):
        self.user_rules = {}
        self.company_rules = {}
        self.regex_rules = {}

    @classmethod
    def get_governance_rules_from_client(cls, api_client, DEBUG):
        try:
            get_rules_response = api_client.get_governance_rules()
            rules = json.loads(get_rules_response.raw_body)
            return rules
        except APIException as inst:
            if 401 <= inst.response_code <= 403:
                print("Unauthorized access getting application configuration. Please check your Appplication Id.")
            if DEBUG:
                print("Error getting governance rules, with status code:", inst.response_code)

        except Exception as ex:
            if DEBUG:
                print("Error getting governance rules:", ex)

    def generate_rules_caching(self, api_client, DEBUG):
        try:
            governance_rules = self.get_governance_rules_from_client(api_client, DEBUG)
            if not governance_rules:
                return None, None, None

            for rule in governance_rules:
                rule_id = rule['_id']

                if 'type' in rule:
                    rule_type = rule['type']
                    if rule_type == 'regex':
                        self.regex_rules[rule_id] = rule
                    elif rule_type == 'user':
                        self.user_rules[rule_id] = rule
                    elif rule_type == 'company':
                        self.company_rules[rule_id] = rule
                    else:
                        print('[moesif] Get parsed rule type {} is not valid'.format(rule['type']))

        except Exception as e:
            print("[moesif] Error when parsing rules response: ", e)

        return self.user_rules, self.company_rules, self.regex_rules
