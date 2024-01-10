import json
from moesifapi import APIException
import logging

logger = logging.getLogger(__name__)

class GovernanceRulesCacher:

    def __init__(self, api_client):
        self.api_client = api_client
        self.user_rules = {}
        self.company_rules = {}
        self.regex_rules = {}

    def get_governance_rules_from_client(self, DEBUG):
        try:
            get_rules_response = self.api_client.get_governance_rules()
            rules = json.loads(get_rules_response.raw_body)
            return rules
        except APIException as inst:
            if 401 <= inst.response_code <= 403:
                logger.error("[moesif] Unauthorized access getting application configuration. Please check your Appplication Id.")
            if DEBUG:
                logger.info(f"[moesif] Error getting governance rules, with status code: {str(inst.response_code)}")
            return None

        except Exception as ex:
            if DEBUG:
                logger.info(f"[moesif] Error getting governance rules: {str(ex)}")
            return None

    def generate_rules_caching(self, DEBUG):
        try:
            governance_rules = self.get_governance_rules_from_client(DEBUG)
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
                        logger.info(f"[moesif] Get parsed rule type {rule['type']} is not valid")

                    self.user_rules = rules_type_mapping['user']
                    self.company_rules = rules_type_mapping['company']
                    self.regex_rules = rules_type_mapping['regex']
        except Exception as e:
            logger.warning(f"[moesif] Error when parsing rules response: {str(e)}")

        return self.user_rules, self.company_rules, self.regex_rules
