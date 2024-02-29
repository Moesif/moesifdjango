from moesifapi.models import *
from moesifapi.exceptions.api_exception import *
from moesifapi.api_helper import *
import logging

logger = logging.getLogger(__name__)

class Subscription: 

    def __init__(self):
        pass

    @classmethod
    def update_subscription(cls, subscription, api_client, DEBUG):
        if not subscription:
            logger.info('Expecting the input to be either of the type - SubscriptionModel, dict or json while updating user')
        else:
            if isinstance(subscription, dict):
                if 'subscription_id' in subscription and 'company_id' in subscription and 'status' in subscription:
                    try:
                        api_client.update_subscription(SubscriptionModel.from_dictionary(subscription))
                        if DEBUG:
                            logger.info('Subscription updated successfully')
                    except APIException as inst:
                        if 401 <= inst.response_code <= 403:
                            logger.error("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                        if DEBUG:
                            logger.info(f"Error while updating subscription, with status code: {str(inst.response_code)}")
                else:
                    logger.info('To update a subscription, a subscription_id, company_id, and status field is required')

            elif isinstance(subscription, SubscriptionModel):
                if subscription.subscription_id is not None and subscription.company_id is not None and subscription.status is not None:
                    try:
                        api_client.update_subscription(subscription)
                        if DEBUG:
                            logger.info('Subscription updated successfully')
                    except APIException as inst:
                        if 401 <= inst.response_code <= 403:
                            logger.error("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                        if DEBUG:
                            logger.info(f"Error while updating subscription, with status code: {str(inst.response_code)}")
                else:
                    logger.info('To update a subscription, a subscription_id, company_id, and status field is required')
            else:
                try:
                    subscription_json = APIHelper.json_deserialize(subscription)
                    if 'subscription_id' in subscription_json and 'company_id' in subscription_json and 'status' in subscription_json:
                        try:
                            api_client.update_subscription(SubscriptionModel.from_dictionary(subscription_json))
                            if DEBUG:
                                logger.info('Subscription updated successfully')
                        except APIException as inst:
                            if 401 <= inst.response_code <= 403:
                                logger.error("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                            if DEBUG:
                                logger.info(f"Error while updating subscription, with status code: {str(inst.response_code)}")
                    else:
                        logger.info('To update a subscription, a subscription_id, company_id, and status field is required')
                except:
                    logger.warning('Error while deserializing the json, please make sure the json is valid')

    @classmethod
    def update_subscriptions_batch(cls, subscriptions, api_client, DEBUG):
        if not subscriptions:
            logger.info('Expecting the input to be a list of either of the type - SubscriptionModel, dict or json while updating user')
        else:
            if isinstance(subscriptions, list):
                try:
                    subscriptions_list = []
                    for subscription in subscriptions:
                        if isinstance(subscription, dict):
                            if 'subscription_id' in subscription and 'company_id' in subscription and 'status' in subscription:
                                subscriptions_list.append(SubscriptionModel.from_dictionary(subscription))
                            else:
                                logger.info('To update a subscription, a subscription_id, company_id, and status field is required')
                        elif isinstance(subscription, SubscriptionModel):
                            if subscription.subscription_id is not None and subscription.company_id is not None and subscription.status is not None:
                                subscriptions_list.append(subscription)
                            else:
                                logger.info('To update a subscription, a subscription_id, company_id, and status field is required')
                        else:
                            try:
                                subscription_json = APIHelper.json_deserialize(subscription)
                                if 'subscription_id' in subscription_json and 'company_id' in subscription_json and 'status' in subscription_json:
                                    subscriptions_list.append(SubscriptionModel.from_dictionary(subscription_json))
                                else:
                                    logger.info('To update a subscription, a subscription_id, company_id, and status field is required')
                            except:
                                logger.warning('Error while deserializing the json, please make sure the json is valid')
                    api_client.update_subscriptions_batch(subscriptions_list)
                    if DEBUG:
                        logger.info('Subscriptions updated successfully')
                except APIException as inst:
                    if 401 <= inst.response_code <= 403:
                        logger.error("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                    if DEBUG:
                        logger.info(f"Error while updating subscriptions, with status code: {str(inst.response_code)}")
            else:
                logger.info('Expecting the input to be a list of either of the type - SubscriptionModel, dict or json while updating user')
