import json
from moesifapi import APIException


class GovernanceRulesCacher:

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
            return None

        except Exception as ex:
            if DEBUG:
                print("Error getting governance rules:", ex)
            return None

    def generate_rules_caching(self, api_client, DEBUG):
        try:
            governance_rules = self.get_governance_rules_from_client(api_client, DEBUG)
            if not governance_rules:
                return None, None, None
            rule_types = ['regex', 'user', 'company']
            rules_type_mapping = {}
            for rule_type in rule_types:
                rules_type_mapping[rule_type] = {}
            for rule in governance_rules:
                rule_id = rule['_id']

                if 'type' in rule:
                    rule_type = rule['type']

                    if rule_type in rule_types:
                        rules_type_mapping[rule_type][rule_id] = rule
                    else:
                        print('[moesif] Get parsed rule type {} is not valid'.format(rule['type']))

                    self.user_rules = rules_type_mapping['user']
                    self.company_rules = rules_type_mapping['company']
                    self.regex_rules = rules_type_mapping['regex']
        except Exception as e:
            print("[moesif] Error when parsing rules response: ", e)

        return self.user_rules, self.company_rules, self.regex_rules
