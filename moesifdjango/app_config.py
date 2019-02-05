from datetime import datetime
import json


# Application Configuration
class AppConfig:
    sampling_percentage = None
    last_updated_time = None
    config_dict = None


def get_config(api_client, config_dict, cached_config_etag):
    """Get Config"""
    sample_rate = 100
    try:
        config_api_response = api_client.get_app_config()
        response_config_etag = config_api_response.headers.get("X-Moesif-Config-ETag")
        if cached_config_etag:
            if cached_config_etag in config_dict: del config_dict[cached_config_etag]
        config_dict[response_config_etag] = json.loads(config_api_response.raw_body)
        app_config = config_dict.get(response_config_etag)
        if app_config is not None:
            sample_rate = app_config.get('sample_rate', 100)
        last_updated_time = datetime.utcnow()
    except:
        last_updated_time = datetime.utcnow()
    return last_updated_time, sample_rate, config_dict


def set_config(updated_time, sample_rate, config_dict):
    """Set global config"""
    AppConfig.last_updated_time = updated_time
    AppConfig.sampling_percentage = sample_rate
    AppConfig.config_dict = config_dict
