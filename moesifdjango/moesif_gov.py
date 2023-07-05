import base64

from django.conf import settings
import json
import re
from .block_response_buffer import BlockResponseBufferList
from .event_mapper import *
from .governance_rule_response import GovernanceRuleBlockResponse
from .governance_rules import AppliedTo, RuleType

REVERSED_PRIORITY_RULES_ORDER = [RuleType.REGEX.value, RuleType.COMPANY.value, RuleType.USER.value]


def merge_block_response(block_response_buffer_list_one: BlockResponseBufferList,
                         block_response_buffer_list_two: BlockResponseBufferList):
    if block_response_buffer_list_one.rule_type != block_response_buffer_list_two.rule_type:
        print('[moesif] Error when merging block response buffer list, [] and [] rule_type are not matching'
              .format(block_response_buffer_list_one.rule_type, block_response_buffer_list_two.rule_type))
        return None
    merged_block_response_buffer_list = block_response_buffer_list_one
    merged_block_response_buffer_list.blocked = block_response_buffer_list_one.blocked \
                                                or block_response_buffer_list_two.blocked

    for response in block_response_buffer_list_two.responses:
        merged_block_response_buffer_list.responses.append(response)

    return merged_block_response_buffer_list


class MoesifGovRuleHelper:
    def __init__(self):
        pass

    @classmethod
    def fetch_entity_rules_from_app_config(cls, config, debug):
        """
        get fetch entity rules from config
        :param config:
        :return: None, if there is no rules in config (no dynamic variable set with gov rules with the app)
                Otherwise, return mapping with keys user_rules and company_rules
        """
        entity_rules = {'user_rules': {}, 'company_rules': {}}
        try:
            raw_body = json.loads(config.raw_body)

            entity_rules = {
                'user_rules': raw_body.get('user_rules', {}),
                'company_rules': raw_body.get('company_rules', {}),
            }
            if debug:
                print(
                    f"[moesif] config got {len(entity_rules['user_rules'])} cohort users and {len(entity_rules['company_rules'])} cohort companies")

        except Exception as e:
            print("[moesif] Error when fetching raw_body from config, ", e)

        return entity_rules

    @classmethod
    def get_entity_governance_rule_and_check_block(cls, entity_rules, governance_rules):
        """
        fetch governance rule object from governance rules list based on entity rules and return the block value (True or False)
        :param entity_rules:
        :param governance_rules:
        :return:
        """
        block_entity_rules = []
        for rules in entity_rules:
            if 'rules' in rules:
                rule_id = rules['rules']
                if rule_id and rule_id in governance_rules:
                    if governance_rules[rule_id]['block']:
                        # if the rule is block checked, then add to the list
                        block_entity_rules.append(rules)
        return block_entity_rules

    @classmethod
    def fetch_governance_rule_response_details(cls, governance_rule, DEBUG):
        if 'response' not in governance_rule \
                or 'status' not in governance_rule['response'] \
                or 'headers' not in governance_rule['response']:
            if DEBUG:
                print(
                    '[moesif] Skipped blocking request as response is not set for the governance rule {} with regex config'.format(
                        governance_rule))
            return None, None, None

        # Response status
        status = governance_rule['response']['status']
        # Response headers
        header = governance_rule['response']['headers']
        body = None
        if 'body' in governance_rule['response']:
            body = governance_rule['response']['body']
        return status, header, body

    def transform_values(self, data, rule_values):
        """
        Replace body value in the response body for the short-circuited request
        :param data:
        :param rule_values:
        :return:
        """
        if data is None:
            return None

        if not rule_values or len(rule_values) == 0:
            return data

        if isinstance(data, str):
            max_index = max(rule_values.keys())

            rule_values_list = [rule_values[key] if key in rule_values.keys() else 'UNKNOWN' for key in
                                range(max_index + 1)]

            try:
                data = data.format(*rule_values_list).format(*rule_values_list)
                return data
            except Exception as e:
                return '[moesif] response body, to get the governance rule response, please try again later'
        if isinstance(data, dict):
            for k, v in data.items():
                data[k] = self.transform_values(v, rule_values)
            return data
        if isinstance(data, list) or isinstance(data, tuple):
            for index in len(data):
                data[index] = self.transform_values(data[index], rule_values)
            return data
        return data

    def regex_pattern_match(self, event_value, condition_value):
        """
        Perform the regex pattern matching with event value and condition value
        :param event_value:
        :param condition_value:
        :return:
        """
        return re.fullmatch(condition_value, event_value) is not None

    # remove the sample rate return value
    def check_request_with_regex_match(self, gr_regex_configs_list, request_mapping_for_regex_config,
                                       ready_for_body_request):
        """
        fetch the sample rate and determine if request is matched with the regex
        :param gr_regex_configs_list:
        :param request_mapping_for_regex_config:
        :param ready_for_body_request:
        :return:
        """
        for or_group_of_regex_rule in gr_regex_configs_list:
            # Fetch the conditions
            conditions = or_group_of_regex_rule.get('conditions', {})
            # fetch the sample rate
            # sample_rate = or_group_of_regex_rule.get('sample_rate', 100)

            # Bool flag to determine if the regex conditions are matched
            regex_matched = None
            # Create a dict to hold the conditions mapping (path and value)
            condition_path_value_mapping = {}

            for condition in conditions:
                try:
                    if 'request.body.' in condition['path']:
                        ok_for_request_body_regex = self.check_if_condition_for_request_body_field(condition)

                        # Add condition path -> value to the condition table
                        if not ok_for_request_body_regex:
                            continue
                    condition_path_value_mapping[condition['path']] = condition['value']

                except KeyError as ke:
                    print('Error when fetching info from regex config each condition: ', ke)
                except Exception as e:
                    print(e)

            # Iterate through conditions table and perform `and` operation between each conditions
            for path, values in condition_path_value_mapping.items():
                try:
                    if re.fullmatch('request\.body\..*', path):
                        if not ready_for_body_request:
                            continue
                except Exception as e:
                    print("[moesif] Error when matching path starts with request\\.body\\", e)

                # Check if the path exists in the request config mapping
                if path in request_mapping_for_regex_config:
                    try:
                        # Fetch the value of the path in request config mapping
                        event_data = request_mapping_for_regex_config[path]
                        # Perform regex matching with event value
                        regex_matched = self.regex_pattern_match(event_data, values)
                    except Exception as e:
                        print("[moesif] Error while matching condition of governance rule {} and event data {}".format(values, e))
                else:
                    # Path does not exist in request config mapping, so no need to match regex condition rule
                    regex_matched = False

                # If one of the rule does not match, skip the condition and avoid matching other rules for the same condition
                if not regex_matched:
                    break

            # If regex conditions matched, return sample rate and block request (true)
            if regex_matched:
                return True

        # If regex conditions are not matched, return default sample rate (nil) and do not block request (false)
        return False

    @classmethod
    def get_req_content_type(cls, request):
        """
        fetch 'content-type' from request headers
        :param request:
        :return:
        """
        lower_case_key_headers =  {k.lower(): v for k, v in request.headers.items()}
        return lower_case_key_headers.get('content-type')

    def ok_request_body_regex_rule(self, request, req_body_transfer_encoding):
        """
        Check if the request body is ready for request.body regex rule
        request.headers.content-type contains “json” and the request body is a JSON object
        (or string/byte buffer that can be parsed as an object)
        :param request:
        :param req_body_transfer_encoding:
        :return: True if we get the special case of request content-type contains grarphql
        and the request body is in type of string
        """
        if not request.body or not req_body_transfer_encoding:
            return False

        content_type_value = self.get_req_content_type(request)
        if isinstance(request.body, str):
            if content_type_value == 'application/graphql':
                return True

        # request.headers.content-type contains “json” and the request body is a JSON object
        # (or string/byte buffer that can be parsed as an object)
        if 'json' not in content_type_value and req_body_transfer_encoding != 'json':
            return False

        return True

    @classmethod
    def check_if_condition_for_request_body_field(cls, condition):
        # check if The field value must be a JSON string
        if not isinstance(condition['value'], str):
            print("[moesif] The field value should be a JSON string")
            return False

        path = condition['path']
        if not isinstance(path, str):
            print("[moesif] The field value should be a JSON string")
            return False

        start = path.find('request.body.')
        if start == -1:
            return False
        start += len('request.body.')
        if '.' in path[start:]:
            print("[moesif] nested fields are not supported for request body condition matching")
            return False

        return True

    def get_updated_response_with_matched_entity_rules(self, governance_rule, rule_and_values, DEBUG):
        """
        get updated response if the entity governance rule is blocked checked, and event matched with request
        utilized by both identified and unidentified
        :param governance_rule:
        :param rule_and_values:
        :return:
        """
        gr_status, gr_header, gr_body = self.fetch_governance_rule_response_details(governance_rule, DEBUG)
        if not gr_status:
            return None, None, None

        # Updated governance rule headers
        updated_gr_headers = {}
        if gr_header:
            for k, v in gr_header.items():
                updated_gr_headers[k] = v

        updated_gr_body = None
        if isinstance(gr_body, str):
            updated_gr_body = gr_body
        elif isinstance(gr_body, dict):
            updated_gr_body = gr_body.copy()

        updated_gr_values = {}
        rule_id = governance_rule.get('_id')
        if rule_id in rule_and_values:
            rule_values = rule_and_values.get(rule_id)
            for k, v in rule_values.items():
                try:
                    updated_gr_values[int(k)] = v
                except Exception as e:
                    print('[moesif] Error when converting entity rules values key: ', e)

        merge_tag_variables = self.merge_tag_variables_rule_mapping(governance_rule)

        # set default value if user/company entity value is None
        for k, v in merge_tag_variables.items():
            if k not in updated_gr_values or not updated_gr_values[k]:
                updated_gr_values[k] = v['default']

        updated_gr_headers = self.transform_values(updated_gr_headers, updated_gr_values)
        updated_gr_body = self.transform_values(updated_gr_body, updated_gr_values)

        return gr_status, updated_gr_headers, updated_gr_body

    def block_request_based_on_entity_governance_rule_identified(self,
                                                                 request_mapping_for_regex_config,
                                                                 ready_for_body_request,
                                                                 governance_rules,
                                                                 rule_type,
                                                                 entity_rules,
                                                                 entity_id,
                                                                 DEBUG):
        """
        Check if need to block request based on the governance rule of the entity associated with the request
        :param rule_type: the type of BlockResponseBufferList (user, company or regex)
        :param request_mapping_for_regex_config:
        :param ready_for_body_request:
        :param governance_rules:
        :param entity_rules:
        :param entity_id: user_id or company_id from event
        :param DEBUG:
        :return: object of updated response status, headers and body, if criteria is matched and block is true, otherwise return None
        """
        response_buffer = BlockResponseBufferList(rule_type)

        for rule_id, _ in entity_rules.items():
            governance_rule = governance_rules.get(rule_id, None)

            if not governance_rule or 'response' not in governance_rule or 'status' not in governance_rule['response']:
                if DEBUG:
                    print(
                        '[moesif] Skipped blocking request as governance rule response is not set for the entity Id - ',
                        entity_id)
                continue

            should_block = self.check_event_should_blocked_by_rule(governance_rule, request_mapping_for_regex_config, ready_for_body_request)

            if not should_block:
                if DEBUG:
                    print(
                        "[moesif] Skipped blocking request because it's not satisfied with {} governance rule {}".format(
                            rule_type,
                            rule_id))
                continue

            # update response status, headers and body if one block rule matched
            updated_gr_status, updated_gr_headers, updated_gr_body = self.get_updated_response_with_matched_entity_rules(
                governance_rule, entity_rules, DEBUG)

            block = governance_rule.get('block', False)
            response_buffer.update(block, updated_gr_status, updated_gr_headers, updated_gr_body, rule_id)

            if DEBUG:
                print("[moesif] request matched with rule_id [{}]".format(rule_id))

        return response_buffer

    def check_event_should_blocked_by_rule(self, governance_rule,
                                           request_mapping_for_regex_config,
                                           ready_for_body_request):
        applied_to = governance_rule.get('applied_to', AppliedTo.MATCHING.value)

        gr_regex_configs = {}
        if "regex_config" in governance_rule and governance_rule["regex_config"]:
            gr_regex_configs = governance_rule["regex_config"]

        matched = self.check_request_with_regex_match(
            gr_regex_configs,
            request_mapping_for_regex_config,
            ready_for_body_request)

        return (matched and applied_to == AppliedTo.MATCHING.value) \
               or (not matched and applied_to == AppliedTo.NOT_MATCHING.value)

    def get_rules_id_if_governance_rule_matched(self, governance_rules, request_mapping_for_regex_config,
                                                ready_for_body_request):
        """
        find the regex governance rules what matched with request, and return the governance rules id
        :param request_mapping_for_regex_config: request config generated from event, for regex config matching in gov rules
        :param governance_rules:
        :param ready_for_body_request:
        :return: list of gov rule ids that event matched
        """
        matched_rules_id = []
        for id, rule in governance_rules.items():

            matched = self.check_event_should_blocked_by_rule(rule, request_mapping_for_regex_config,
                                                              ready_for_body_request)

            if matched:
                matched_rules_id.append(id)
        return matched_rules_id

    def block_request_based_on_regex_or_unidentified_entity_governance_rule(self,
                                                                            request_mapping_for_regex_config,
                                                                            ready_for_body_request,
                                                                            regex_governance_rules,
                                                                            rule_type,
                                                                            entity_rules,
                                                                            DEBUG):
        """
        Check if need to block request based on the governance rule regex config associated with the request
        :param entity_rules: specific entity rules config {"rule_id": "values for merge tag"}, if merge tag is defined
        :param rule_type: (user, company or regex)
        :param request_mapping_for_regex_config:
        :param ready_for_body_request:
        :param regex_governance_rules:
        :param DEBUG:
        :return:
        """

        response_buffer = BlockResponseBufferList(rule_type)
        matched_rules_id = self.get_rules_id_if_governance_rule_matched(regex_governance_rules,
                                                                        request_mapping_for_regex_config,
                                                                        ready_for_body_request)

        if not matched_rules_id:
            if DEBUG:
                print('[moesif] no regex rule matched with the request')
        else:
            for rule_id in matched_rules_id:
                governance_rule = regex_governance_rules.get(rule_id)
                if not governance_rule:
                    if DEBUG:
                        print(
                            '[moesif] Skipped blocking request as rule {} is not found'.format(rule_id))
                    continue

                block = governance_rule.get('block', False)
                gr_status, gr_header, gr_body = \
                    self.get_updated_response_with_matched_entity_rules(governance_rule, entity_rules, DEBUG)

                response_buffer.update(block, gr_status, gr_header, gr_body, rule_id)
                if DEBUG:
                    print('[moesif] request matched with regex rule with rule_id {}'.format(rule_id))

        return response_buffer

    # TODO can deal with request.body in one place
    @classmethod
    def prepare_request_config_based_on_regex_config(cls, event: EventModel, ready_for_body_request):
        """
        fetch regex config from config mapping
        :param event:
        :param ready_for_body_request:
        :return:
        """
        regex_config = {}
        # Config mapping for request.verb
        if event.request.verb:
            regex_config["request.verb"] = event.request.verb

        # Config mapping for request.uri
        if event.request.uri:
            extracted = re.match("http[s]*://[^/]+(/[^?]+)", event.request.uri)
            extracted_string = None
            if not extracted:
                extracted_string = '/'
            else:
                extracted_string = extracted.string
            regex_config["request.route"] = extracted_string

        # Config mapping for request.ip_address
        if event.request.ip_address:
            regex_config["request.ip_address"] = event.request.ip_address

        # DONE Add GraphQL Operation Name
        if event.request.body:
            if 'operationName' in event.request.body:
                regex_config['request.body.operationName'] = event.request.body['operationName']
            if isinstance(event.request.body, dict) and ready_for_body_request:
                if 'query' in event.request.body:
                    regex_config['request.body.query'] = event.request.body['query']
            elif isinstance(event.request.body, str) and ready_for_body_request:
                regex_config['request.body.query'] = base64.b64decode(event.request.body).decode('utf-8')

        # Config mapping for response.status
        if event.response.status:
            regex_config['response.status'] = event.response.status

        return regex_config

    def generate_blocking_response(self, response_buffers):
        """
        rearrange matching rules' response, merge all the headers, and ordered by the rules type priority
        updated response_body and response_status with the highest priority blocked rule

        :param response_buffers:
        :return: None if none of the rules is blocking request, otherwise return the blocking response
        """
        if not self.check_if_request_blocked(response_buffers):
            return None

        updated_body = None
        updated_status = None
        updated_headers = {}
        blocked_by = None
        blocked = False

        for rule_type in REVERSED_PRIORITY_RULES_ORDER:
            if rule_type in response_buffers:
                buffer = response_buffers.get(rule_type, None)
                if buffer:
                    responses = buffer.responses
                    for response in responses:
                        if response.blocked:
                            updated_body = response.block_response_body
                            updated_status = response.block_response_status
                            blocked_by = response.blocked_by
                            blocked = response.blocked
                        updated_headers.update(response.block_response_headers)

        gov_rule_response = GovernanceRuleBlockResponse()
        gov_rule_response.update_response(updated_status, updated_headers, updated_body, blocked, blocked_by)
        return gov_rule_response

    @classmethod
    def check_if_request_blocked(cls, response_buffers):
        for rule_type in REVERSED_PRIORITY_RULES_ORDER:
            if rule_type in response_buffers:
                response = response_buffers[rule_type]
                if response.blocked:
                    return True
        return False

    @classmethod
    def merge_tag_variables_rule_mapping(cls, governance_rule):
        merge_tag_variables = {}
        variables = governance_rule.get('variables', [])
        for variable in variables:
            try:
                name = int(variable['name'])
                path = variable['path']
                default_value = variable.get('default', 'UNKNOWN')
                merge_tag_variables.update(
                    {
                        name: {
                            'path': path,
                            'default': default_value
                        }
                    }
                )
            except Exception as e:
                print('[moesif] Error when parsing rule {} variable'.format(governance_rule.get('id')), e)
        return merge_tag_variables

    @classmethod
    def get_entity_rule_mapping_from_config(cls, entity_rules, rule_type_in_config, entity_id):
        rule_merge_tag_values_mapping = {}
        try:
            if entity_id:
                rules_mapping_from_config = entity_rules[rule_type_in_config][entity_id]
                for rule_values in rules_mapping_from_config:
                    rule_id = rule_values['rules']
                    if rule_id not in rule_merge_tag_values_mapping:
                        rule_merge_tag_values_mapping[rule_id] = {}
                    if 'values' in rule_values:
                        values = rule_values['values']
                        rule_merge_tag_values_mapping[rule_id].update(values)

        except Exception as e:
            print('[moesif] Skipped blocking request, Error when fetching entity rule with entity {}, {}'.format(
                entity_id, e))
        return rule_merge_tag_values_mapping

    def apply_governance_rules(self,
                               event,
                               user_id_entity, company_id_entity,
                               req_body_transfer_encoding,
                               entity_rules,
                               identified_user_governance_rules,
                               unidentified_user_governance_rules,
                               identified_company_governance_rules,
                               unidentified_company_governance_rules,
                               regex_governance_rules,
                               DEBUG):

        ready_for_body_request = self.ok_request_body_regex_rule(event.request, req_body_transfer_encoding)
        request_mapping_for_regex_config = self.prepare_request_config_based_on_regex_config(event,
                                                                                             ready_for_body_request)

        user_rules_mapping_from_config = self.get_entity_rule_mapping_from_config(entity_rules, 'user_rules',
                                                                                  user_id_entity)
        company_rules_mapping_from_config = self.get_entity_rule_mapping_from_config(entity_rules, 'company_rules',
                                                                                     company_id_entity)

        response_buffers = {
            RuleType.REGEX.value: BlockResponseBufferList(RuleType.REGEX.value),
            RuleType.COMPANY.value: BlockResponseBufferList(RuleType.COMPANY.value),
            RuleType.USER.value: BlockResponseBufferList(RuleType.USER.value)
        }
        if regex_governance_rules:
            regex_response_buffer = self.block_request_based_on_regex_or_unidentified_entity_governance_rule(
                request_mapping_for_regex_config,
                ready_for_body_request,
                regex_governance_rules,
                RuleType.REGEX.value,
                {},
                DEBUG)
            if not regex_response_buffer.blocked:
                if DEBUG:
                    print('[moesif] No matching with the request from regex rules')

            response_buffers[RuleType.REGEX.value] = regex_response_buffer
        else:
            if DEBUG:
                print('[moesif] No regex rules')

        if unidentified_company_governance_rules:
            if not company_id_entity:
                unidentified_company_response_buffer = \
                    self.block_request_based_on_regex_or_unidentified_entity_governance_rule(
                        request_mapping_for_regex_config,
                        ready_for_body_request,
                        unidentified_company_governance_rules,
                        RuleType.COMPANY.value,
                        company_rules_mapping_from_config,
                        DEBUG
                    )
            else:
                unidentified_company_response_buffer = \
                    self.block_request_based_on_entity_governance_rule_identified(
                        request_mapping_for_regex_config,
                        ready_for_body_request,
                        unidentified_company_governance_rules,
                        RuleType.COMPANY.value,
                        company_rules_mapping_from_config,
                        company_id_entity,
                        DEBUG)
            if not unidentified_company_response_buffer or not unidentified_company_response_buffer.blocked:
                if DEBUG:
                    print('[moesif] No matching with the request from unidentified company rules for {}'
                          .format(company_id_entity if company_id_entity else 'unidentified company'))
            else:
                response_buffers[RuleType.COMPANY.value] = unidentified_company_response_buffer
        else:
            if DEBUG:
                print('[moesif] no unidentified company governance rules')

        if company_id_entity and identified_company_governance_rules:
            company_response_buffer = self.block_request_based_on_entity_governance_rule_identified(
                request_mapping_for_regex_config,
                ready_for_body_request,
                identified_company_governance_rules,
                RuleType.COMPANY.value,
                company_rules_mapping_from_config,
                company_id_entity,
                DEBUG)
            if not company_response_buffer.blocked:
                if DEBUG:
                    print('[moesif] No matching with the request from identified company rules for {}'.format(company_id_entity))
            else:
                response_buffers[RuleType.COMPANY.value] = merge_block_response(
                    response_buffers.get(RuleType.COMPANY.value, BlockResponseBufferList()),
                    company_response_buffer)
        else:
            if DEBUG:
                print('[moesif] company_id is unidentified or no identified company governance rules')

        if unidentified_user_governance_rules:
            if not user_id_entity:
                unidentified_user_response_buffer = \
                    self.block_request_based_on_regex_or_unidentified_entity_governance_rule(
                        request_mapping_for_regex_config,
                        ready_for_body_request,
                        unidentified_user_governance_rules,
                        RuleType.USER.value,
                        user_rules_mapping_from_config,
                        DEBUG
                    )
            else:
                unidentified_user_response_buffer = self.block_request_based_on_entity_governance_rule_identified(
                    request_mapping_for_regex_config,
                    ready_for_body_request,
                    unidentified_user_governance_rules,
                    RuleType.USER.value,
                    user_rules_mapping_from_config,
                    user_id_entity,
                    DEBUG)
            if not unidentified_user_response_buffer or not unidentified_user_response_buffer.blocked:
                if DEBUG:
                    print('[moesif] No matching with the request from unidentified user rules for {}'.format(
                        user_id_entity if user_id_entity else "unidentified user"
                    ))
            else:
                response_buffers[RuleType.USER.value] = unidentified_user_response_buffer
        else:
            if DEBUG:
                print('[moesif] No unidentified user governance rules')

        if user_id_entity and identified_user_governance_rules:
            identified_user_response_buffer = self.block_request_based_on_entity_governance_rule_identified(
                request_mapping_for_regex_config,
                ready_for_body_request,
                identified_user_governance_rules,
                RuleType.USER.value,
                user_rules_mapping_from_config,
                user_id_entity,
                DEBUG)

            if not identified_user_response_buffer.blocked:
                if DEBUG:
                    print('[moesif] No matching with the request from identified user rules for {}'.format(
                        user_id_entity))
            else:
                response_buffers[RuleType.USER.value] = merge_block_response(
                    response_buffers.get(RuleType.USER.value, BlockResponseBufferList()),
                    identified_user_response_buffer)
        else:
            if DEBUG:
                print('[moesif] user_id is unidentified or no identified user governance rules')

        blocking_response = self.generate_blocking_response(response_buffers)

        return blocking_response
