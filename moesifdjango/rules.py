from moesifapi import APIException


class Rule:
    def __init__(self):
        pass

    @classmethod
    def get_rules(cls, api_client, DEBUG):
        try:
            get_rules_response = api_client.get_governance_rules()
            return get_rules_response
        except APIException as inst:
            if 401 <= inst.response_code <= 403:
                print("Unauthorized access getting application configuration. Please check your Appplication Id.")
            if DEBUG:
                print("Error getting application configuration, with status code:")
                print(inst.response_code)

        except Exception as ex:
            if DEBUG:
                print("Error getting application configuration:")
                print(str(ex))