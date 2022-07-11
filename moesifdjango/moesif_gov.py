import base64

from django.conf import settings
import json
import re
from .event_mapper import *

middleware_settings = settings.MOESIF_MIDDLEWARE
hash_key = middleware_settings.get('APPLICATION_ID')[-10:]  # may need concern about scope

REVERSED_PRIORITY_RULES_ORDER = ['regex', 'company', 'user']


class GovernanceRuleBlockResponse:
    def __init__(self, gr_status, gr_headers, gr_body, block):
        self.block_response_status = gr_status
        self.block_response_headers = gr_headers
        self.block_response_body = gr_body
        self.blocked = block


class BlockResponseBufferList:
    def __init__(self):
        self.responses = []
        self.rule_type = None
        self.blocked = False

    def update(self, block, updated_gr_status, updated_gr_headers, updated_gr_body):
        if not self.rule_type:
            self.rule_type = 'regex'
        if block and not self.blocked:
            self.blocked = True
        self.responses.append(
            GovernanceRuleBlockResponse(updated_gr_status, updated_gr_headers, updated_gr_body, block))


'''
    get fetch entity rules from config

'''


def fetch_entity_rules_from_app_config(config):
    entity_rules = {}
    try:
        raw_body = json.loads(config.raw_body)

        try:
            user_rules = raw_body['user_rules']
            if user_rules:
                entity_rules['user_rules'] = user_rules
        except KeyError:
            print(f"[moesif] {raw_body}'s attribute [user_rules] is unknown.")

        try:
            company_rules = raw_body['company_rules']
            if company_rules:
                entity_rules['company_rules'] = company_rules
        except KeyError:
            print(f"[moesif] {raw_body}'s attribute [company_rules] is unknown.")

    except KeyError:
        print(f"[moesif] config attribute ['raw_body'] is unknown.")

    return entity_rules


def get_governance_rules_from_hashes(governance_rules_hashes, entity_rules, entity_id, rule_name, DEBUG):
    if hash_key not in governance_rules_hashes or hash_key not in entity_rules \
            or rule_name not in entity_rules[hash_key]:
        if DEBUG:
            print(
                '[moesif] Skipped blocking request as no governance rules found for the entity associated with the request.')
        return None, None

    governance_rules = governance_rules_hashes[hash_key]
    try:
        entity_rules = entity_rules[hash_key][rule_name][entity_id]
    except Exception as e:
        print('Error when getting entity rules: ', e)

    # Fetch governance rules which is blocked, if no rules with entity, return None
    block_checked_entity_rules = get_entity_governance_rule_and_check_block(entity_rules, governance_rules)

    if not block_checked_entity_rules:
        if DEBUG:
            print(
                '[moesif] Skipped blocking request as no governance rule found or for none of the governance rule block is set to true for the entity Id - ',
                entity_id)
        return None, None

    return governance_rules, block_checked_entity_rules


'''
    fetch governance rule object from governance rules list based on entity rules and return the block value (True or False)
'''


def get_entity_governance_rule_and_check_block(entity_rules, governance_rules):
    block_entity_rules = []
    for rules in entity_rules:
        if 'rules' in rules:
            rule_id = rules['rules']
            if rule_id and rule_id in governance_rules:
                if governance_rules[rule_id]['block']:
                    # if the rule is block checked, then add to the list
                    block_entity_rules.append(rules)
    return block_entity_rules


def fetch_governance_rule_response_details(governance_rule):
    # Response status
    status = governance_rule['response']['status']
    # Response headers
    header = governance_rule['response']['headers']
    body = None
    if 'body' in governance_rule['response']:
        body = governance_rule['response']['body']
    return status, header, body


'''
    Replace body value in the response body for the short-circuited request
'''


def transform_values(data, rule_values):
    if data is None:
        return None
    if isinstance(data, str):
        max_index = max(rule_values.keys())

        rule_values_list = [rule_values[key] if key in rule_values.keys() else None for key in
                            range(max_index + 1)]

        try:
            data = data.format(*rule_values_list).format(*rule_values_list)
            return data
        except Exception as e:
            return '[moesif] response body, to get the governance rule response, please try again later'
    if isinstance(data, dict):
        for k, v in data.items():
            data[k] = transform_values(v, rule_values)
        return data
    if isinstance(data, list) or isinstance(data, tuple):
        for index in len(data):
            data[index] = transform_values(data[index], rule_values)
        return data
    return data


'''
    Perform the regex matching with event value and condition value
'''


def regex_match(event_value, condition_value):
    return event_value == condition_value


'''
    Perform the regex pattern matching with event value and condition value
'''


def regex_pattern_match(event_value, condition_value):
    return re.search(condition_value, event_value) is not None


'''
    fetch the sample rate and determine if request is matched with the regex
'''


# remove the sample rate return value
def check_request_with_regex_match(gr_regex_configs_list, request_mapping_for_regex_config,
                                   ready_for_body_request):
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
                    ok_for_request_body_regex = check_if_condition_for_request_body_field(condition)

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
            if re.fullmatch('request\.body\..*', path):
                if not ready_for_body_request:
                    continue

            # Check if the path exists in the request config mapping
            if path in request_mapping_for_regex_config:
                # Fetch the value of the path in request config mapping
                event_data = request_mapping_for_regex_config[path]
                # Perform regex matching with event value
                regex_matched = regex_pattern_match(event_data, values)
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


'''
    check if the request config mapping governance rule regex conditions
'''


def check_event_matched_with_governance_rules(gr_regex_configs, request_mapping_for_regex_config,
                                              ready_for_body_request):
    matched = check_request_with_regex_match(gr_regex_configs,
                                             request_mapping_for_regex_config,
                                             ready_for_body_request)

    return matched


'''
    fetch 'content-type' from request headers
'''


def get_req_content_type(request):
    if 'content-type' in request.headers:
        return request.headers['content-type']
    if 'Content-Type' in request.headers:
        return request.headers['Content-Type']
    if 'CONTENT-TYPE' in request.headers:
        return request.headers['CONTENT-TYPE']
    return None


'''
    Check if the request body is ready for request.body regex rule
    request.headers.content-type contains “json” and the request body is a JSON object 
    (or string/byte buffer that can be parsed as an object)
    
    also return true if we get the special case of request content-type contains grarphql
    and the request body is in type of string
'''


def ok_request_body_regex_rule(request, req_body_transfer_encoding):
    if not request.body or not req_body_transfer_encoding:
        return False

    content_type_value = get_req_content_type(request)
    if isinstance(request.body, str):
        if 'graphql' in content_type_value:
            return True

    # request.headers.content-type contains “json” and the request body is a JSON object
    # (or string/byte buffer that can be parsed as an object)
    if 'json' not in content_type_value and req_body_transfer_encoding != 'json':
        return False

    return True


def check_if_condition_for_request_body_field(condition):
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
        print("Moesif does not support nested fields")
        return False

    return True


'''
    get updated response if the governance is blocked checked and matched with request
'''


def get_updated_response_with_matched_rules(governance_rule, rule_and_values):
    gr_status, gr_header, gr_body = fetch_governance_rule_response_details(governance_rule)

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
    if 'values' in rule_and_values and rule_and_values['values']:
        rule_values = rule_and_values['values']
        for k, v in rule_values.items():
            try:
                updated_gr_values[int(k)] = v
            except Exception as e:
                print('Error when converting entity rules values key: ', e)

        updated_gr_headers = transform_values(updated_gr_headers, updated_gr_values)
        updated_gr_body = transform_values(updated_gr_body, updated_gr_values)

    return gr_status, updated_gr_headers, updated_gr_body


'''
    Check if need to block request based on the governance rule of the entity associated with the request
    
    returns:
        object of updated response status, headers and body, if criteria is matched and block is true, otherwise return None
    
'''


def block_request_based_on_entity_governance_rule(request_mapping_for_regex_config,
                                                  ready_for_body_request,
                                                  governance_rules,
                                                  entity_rules,
                                                  rule_entity_type,
                                                  entity_id,
                                                  DEBUG):
    entity_rules = entity_rules[rule_entity_type][entity_id]

    response_buffer = BlockResponseBufferList()
    for rule_and_values in entity_rules:
        rule_id = rule_and_values['rules']
        governance_rule = governance_rules[rule_id]

        if 'response' not in governance_rule or 'status' not in governance_rule['response'] \
                or 'headers' not in governance_rule['response']:
            if DEBUG:
                print('[moesif] Skipped blocking request as governance rule response is not set for the entity Id - ',
                      entity_id)
            return None

        gr_regex_configs = {}
        if "regex_config" in governance_rule and governance_rule["regex_config"]:
            gr_regex_configs = governance_rule["regex_config"]

        matched = check_event_matched_with_governance_rules(gr_regex_configs, request_mapping_for_regex_config,
                                                            ready_for_body_request)

        if not matched:
            if DEBUG:
                print("[moesif] Skipped blocking request as governance rule {} regex conditions does not match".format(
                    rule_id))
            continue

        # update response status, headers and body if one block rule matched
        updated_gr_status, updated_gr_headers, updated_gr_body = get_updated_response_with_matched_rules(
            governance_rule, rule_and_values)

        block = governance_rule.get('block', False)
        response_buffer.update(block, updated_gr_status, updated_gr_headers, updated_gr_body)

        if DEBUG:
            print("[moesif] request matched with rule_id [{}]".format(rule_id))

    return response_buffer


'''
    find the regex governance rules what matched with request, and return the governance rules id
'''


def get_rules_id_if_governance_rule_matched(regex_governance_rules, event, ready_for_body_request):
    matched_rules_id = []
    request_config_mapping = prepare_request_config_based_on_regex_config(event, ready_for_body_request)
    for id, rule in regex_governance_rules.items():
        if 'regex_config' not in rule or not rule['regex_config']:
            continue
        regex_configs = rule['regex_config']

        matched = check_request_with_regex_match(regex_configs, request_config_mapping,
                                                 ready_for_body_request)

        if matched:
            try:
                matched_rules_id.append(rule['_id'])
            except KeyError as ke:
                print('Error when fetching matched regex governance rule ', ke)

    return matched_rules_id


'''
    Check if need to block request based on the governance rule regex config associated with the request
'''


def block_request_based_on_governance_rule_regex_config(event, ready_for_body_request, regex_governance_rules, DEBUG):
    response_buffer = BlockResponseBufferList()
    matched_rules_id = get_rules_id_if_governance_rule_matched(regex_governance_rules, event,
                                                               ready_for_body_request)

    if not matched_rules_id:
        if DEBUG:
            print('[moesif] no regex rule matched with the request')
    else:
        for rule_id in matched_rules_id:
            governance_rule = regex_governance_rules[rule_id]
            if not governance_rule:
                if DEBUG:
                    print(
                        '[moesif] Skipped blocking request as rule {} is not found'.format(rule_id))
                    continue

            if 'response' not in governance_rule \
                    or 'status' not in governance_rule['response'] \
                    or 'headers' not in governance_rule['response']:
                if DEBUG:
                    print(
                        '[moesif] Skipped blocking request as response is not set for the governance rule with regex config')
                continue

            block = governance_rule.get('block', False)
            gr_status, gr_header, gr_body = fetch_governance_rule_response_details(governance_rule)

            response_buffer.update(block, gr_status, gr_header, gr_body)
            if DEBUG:
                print('request matched with regex rule with rule_id {}'.format(rule_id))
    return response_buffer


'''
    fetch regex config from config mapping
'''


# TODO can deal with request.body in one place
def prepare_request_config_based_on_regex_config(event: EventModel, ready_for_body_request):
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
        regex_config["response.status"] = event.response.status

    return regex_config


'''
    All matching rules' response:
    merge all of the headers, and ordered by the rules type priority 
    updated response_body and response_status with the highest priority blocked rule

    Return None if none of the rules is blocking request, otherwise return the blocking response             
'''


def generate_blocking_response(response_buffers):
    if not check_if_request_blocked(response_buffers):
        return None

    updated_body = None
    updated_status = None
    updated_headers = {}

    for rule_type in REVERSED_PRIORITY_RULES_ORDER:
        if rule_type in response_buffers:
            responses = response_buffers[rule_type].responses
            for response in responses:
                if response.blocked:
                    updated_body = response.block_response_body
                    updated_status = response.block_response_status
                updated_headers.update(response.block_response_headers)

    return GovernanceRuleBlockResponse(updated_status, updated_headers, updated_body, True)


def check_if_request_blocked(response_buffers):
    for rule_type in REVERSED_PRIORITY_RULES_ORDER:
        if rule_type in response_buffers:
            response = response_buffers[rule_type]
            if response.blocked:
                return True
    return False


def govern_request(event,
                   user_id, company_id,
                   req_body_transfer_encoding,
                   entity_rules,
                   user_governance_rules,
                   company_governance_rules,
                   regex_governance_rules,
                   DEBUG):
    user_id_entity = user_id
    company_id_entity = company_id

    ready_for_body_request = ok_request_body_regex_rule(event.request, req_body_transfer_encoding)
    request_mapping_for_regex_config = prepare_request_config_based_on_regex_config(event, ready_for_body_request)

    response_buffers = {}
    if regex_governance_rules:
        regex_response_buffer = block_request_based_on_governance_rule_regex_config(event,
                                                                                    ready_for_body_request,
                                                                                    regex_governance_rules,
                                                                                    DEBUG)
        if not regex_response_buffer.blocked:
            if DEBUG:
                print('[moesif] No matching with the request from regex rules')

        response_buffers['regex'] = regex_response_buffer
    else:
        if DEBUG:
            print('[moesif] No regex rules')

    if company_id_entity and company_governance_rules:
        company_response_buffer = block_request_based_on_entity_governance_rule(request_mapping_for_regex_config,
                                                                                ready_for_body_request,
                                                                                company_governance_rules,
                                                                                entity_rules,
                                                                                'company_rules',
                                                                                company_id_entity,
                                                                                DEBUG)
        if not company_response_buffer.blocked:  # No match or No need block
            if DEBUG:
                print('[moesif] No blocking from company: ', company_id_entity)

        response_buffers['company'] = company_response_buffer
    else:
        if DEBUG:
            print('[moesif] company_id is not valid or no governance rules for the company')

    if user_id_entity and user_governance_rules:
        user_response_buffer = block_request_based_on_entity_governance_rule(request_mapping_for_regex_config,
                                                                             ready_for_body_request,
                                                                             user_governance_rules,
                                                                             entity_rules,
                                                                             'user_rules',
                                                                             user_id_entity,
                                                                             DEBUG)

        if not user_response_buffer.blocked:
            if DEBUG:
                print('[moesif] No blocking from user: ', user_id_entity)

        response_buffers['user'] = user_response_buffer
    else:
        if DEBUG:
            print('[moesif] user_id is not valid or no governance rules for the user')

    blocking_response = generate_blocking_response(response_buffers)

    return blocking_response
