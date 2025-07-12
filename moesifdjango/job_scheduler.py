from datetime import datetime
from moesifapi.app_config.app_config import AppConfig
import logging

logger = logging.getLogger(__name__)

class JobScheduler:

    def __init__(self):
        self.app_config = AppConfig()

    @classmethod
    def exit_handler(cls, scheduler, debug):
        try:
            # Remove job and shut down the scheduler
            scheduler.remove_job('moesif_events_batch_job')
            scheduler.shutdown()
        except Exception as ex:
            if debug:
                logger.info(f"Error while closing the queue or scheduler shut down {str(ex)}")

    def send_events(self, api_client, batch_events, debug):
        try:
            if debug:
                logger.info("Sending events to Moesif")
            batch_events_api_response = api_client.create_events_batch(batch_events)
            if debug:
                logger.info("Events sent successfully")
            # Fetch Config ETag from response header
            batch_events_response_config_etag = batch_events_api_response.get("X-Moesif-Config-ETag")
            batch_events_response_rule_etag = batch_events_api_response.get("X-Moesif-Rules-Tag", None)
            # Return Config Etag
            return batch_events_response_config_etag, batch_events_response_rule_etag
        except Exception as ex:
            if debug:
                logger.info(f"Error sending event to Moesif: {str(ex)}")
            return None

    # Function to fetch application config
    def fetch_app_config(self, config, config_etag, sampling_percentage, last_updated_time, api_client, debug):
        try:
            config = self.app_config.get_config(api_client, debug)
            if config:
                config_etag, sampling_percentage, last_updated_time = self.app_config.parse_configuration(config, debug)
        except Exception as e:
            if debug:
                logger.info(f'Error while fetching the application configuration: {str(e)}')
        return config, config_etag, sampling_percentage, last_updated_time


    def batch_events(self, api_client, moesif_events_queue, debug, batch_size):
        batch_events = []
        try:
            while not moesif_events_queue.empty():
                batch_events.append(moesif_events_queue.get_nowait())
                if len(batch_events) == batch_size:
                    break

            if batch_events:
                req_time = batch_events[0].request.time
                req_time = datetime.strptime(req_time, '%Y-%m-%dT%H:%M:%S.%f')
                batch_response_config_etag, batch_response_rules_etag = self.send_events(api_client, batch_events, debug)
                batch_events[:] = []
                # Set the last time event job ran after sending events
                batch_send_time = datetime.utcnow()
                delta = batch_send_time - req_time
                if debug and delta.total_seconds() > 60:
                    logger.info("Warning: It took %s seconds to send events to Moesif. req.time=%s now=%s"%(delta.total_seconds(), req_time, batch_send_time))
                return batch_response_config_etag, batch_response_rules_etag, batch_send_time
            else:
                # Set the last time event job ran but no message to read from the queue
                return None, None, datetime.utcnow()
        except Exception as e:
            if debug:
                logger.info(f"No message to read from the queue: {str(e)}")
            # Set the last time event job ran when exception occurred while sending event
            return None, None, datetime.utcnow()
