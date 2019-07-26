from datetime import datetime
import json
from moesifapi.exceptions.api_exception import *

# Application Configuration
class AppConfig:

    def get_config(self, api_client, debug):
        """Get Config"""
        try:
            config_api_response = api_client.get_app_config()
            return config_api_response
        except APIException as inst:
            if 401 <= inst.response_code <= 403:
                print("Unauthorized access getting application configuration. Please check your Appplication Id.")
            if debug:
                print("Error sending event to Moesif, with status code:")
                print(inst.response_code)

    def parse_configuration(self, config, debug):
        """Parse configuration object and return Etag, sample rate and last updated time"""
        try:
            return config.headers.get("X-Moesif-Config-ETag"), json.loads(config.raw_body).get('sample_rate', 100), datetime.utcnow()
        except:
            if debug:
                print('Error while parsing the configuration object, setting the sample rate to default')
            return None, 100, datetime.utcnow()
