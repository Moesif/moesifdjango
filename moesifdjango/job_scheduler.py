from datetime import datetime
from .app_config import AppConfig

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
                print("Error while closing the queue or scheduler shut down")
                print(str(ex))

    def send_events(self, api_client, batch_events, debug):
        try:
            if debug:
                print("Sending events to Moesif")
            batch_events_api_response = api_client.create_events_batch(batch_events)
            if debug:
                print("Events sent successfully")
            # Fetch Config ETag from response header
            batch_events_response_config_etag = batch_events_api_response.get("X-Moesif-Config-ETag")
            # Return Config Etag
            return batch_events_response_config_etag
        except Exception as ex:
            if debug:
                print("Error sending event to Moesif")
                print(str(ex))
            return None

    # Function to fetch application config
    def fetch_app_config(self, config, config_etag, sampling_percentage, last_updated_time, api_client, debug):
        try:
            config = self.app_config.get_config(api_client, debug)
            if config:
                config_etag, sampling_percentage, last_updated_time = self.app_config.parse_configuration(config, debug)
        except Exception as e:
            if debug:
                print('Error while fetching the application configuration')
                print(str(e))
        return config, config_etag, sampling_percentage, last_updated_time

    def batch_events(self, api_client, moesif_events_queue, debug, batch_size):
        # Set the last time event job ran
        last_event_job_run_time = datetime.utcnow()

        batch_events = []
        try:
            while not moesif_events_queue.empty():
                batch_events.append(moesif_events_queue.get_nowait())
                if len(batch_events) == batch_size:
                    break

            if batch_events:
                batch_response = self.send_events(api_client, batch_events, debug)
                batch_events[:] = []
                return batch_response, last_event_job_run_time
            else:
                if debug:
                    print("No events to send")
                return None, last_event_job_run_time
        except:
            if debug:
                print("No message to read from the queue")
            return None, last_event_job_run_time
