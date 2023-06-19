import json
from moesifapi import APIException
from enum import Enum


class AppliedTo(Enum):
    MATCHING = 'matching'
    NOT_MATCHING = 'not_matching'


class RuleType(Enum):
    USER = 'user'
    COMPANY = 'company'
    REGEX = 'regex'


class GovernanceRulesCacher:

    def __init__(self, api_client):
        self.api_client = api_client
        self.applied_to_identified_user_rules = {}
        self.applied_to_identified_company_rules = {}
        self.applied_to_unidentified_user_rules = {}
        self.applied_to_unidentified_company_rules = {}
        self.regex_rules = {}

    def get_governance_rules_from_client(self, DEBUG):
        try:
            get_rules_response = self.api_client.get_governance_rules()
            rules = json.loads(get_rules_response.raw_body)
            return rules
        except APIException as inst:
            if 401 <= inst.response_code <= 403:
                print("[moesif] Unauthorized access getting application configuration. Please check your Appplication Id.")
            if DEBUG:
                print("[moesif] Error getting governance rules, with status code:", inst.response_code)
            return None

        except Exception as ex:
            if DEBUG:
                print("[moesif] Error getting governance rules:", ex)
            return None

    def generate_rules_caching(self, DEBUG):
        try:
            governance_rules = self.get_governance_rules_from_client(DEBUG)
            if not governance_rules:
                return None, None, None
            rule_types = [RuleType.REGEX.value, RuleType.USER.value, RuleType.COMPANY.value]
            rules_type_mapping = {}
            for rule_type in rule_types:
                if rule_type == RuleType.REGEX.value:
                    rules_type_mapping[rule_type] = {}
                    rules_type_mapping[rule_type][False] = {}
                else:
                    rules_type_mapping[rule_type] = {}
                    rules_type_mapping[rule_type][True] = {}
                    rules_type_mapping[rule_type][False] = {}
            for rule in governance_rules:
                rule_id = rule['_id']

                if 'type' in rule:
                    rule_type = rule['type']

                    if rule_type in rule_types:
                        applied_to_unidentified = rule.get('applied_to_unidentified', False)
                        rules_type_mapping[rule_type][applied_to_unidentified][rule_id] = rule
                    else:
                        print('[moesif] Get parsed rule type {} is not valid'.format(rule['type']))

            self.applied_to_identified_user_rules = rules_type_mapping[RuleType.USER.value][False]
            self.applied_to_unidentified_user_rules = rules_type_mapping[RuleType.USER.value][True]
            self.applied_to_identified_company_rules = rules_type_mapping[RuleType.COMPANY.value][False]
            self.applied_to_unidentified_company_rules = rules_type_mapping[RuleType.COMPANY.value][True]
            # regex rule will not apply to unidentified or identified, currently,
            # we will consider that the applied_to_unidentified always set to False
            self.regex_rules = rules_type_mapping[RuleType.REGEX.value][False]
        except Exception as e:
            print("[moesif] Error when parsing rules response: ", e)

        return self.applied_to_identified_user_rules, self.applied_to_unidentified_user_rules, \
               self.applied_to_identified_company_rules, self.applied_to_unidentified_company_rules, \
               self.regex_rules
