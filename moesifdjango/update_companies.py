from moesifapi.models import *
from moesifapi.exceptions.api_exception import *
from moesifapi.api_helper import *
import logging

logger = logging.getLogger(__name__)


class Company:

    def __init__(self):
        pass

    @classmethod
    def update_company(cls, company_profile, api_client, DEBUG):
        if not company_profile:
            logger.info('Expecting the input to be either of the type - CompanyModel, dict or json while updating user')
        else:
            if isinstance(company_profile, dict):
                if 'company_id' in company_profile:
                    try:
                        api_client.update_company(CompanyModel.from_dictionary(company_profile))
                        if DEBUG:
                            logger.info('Company Profile updated successfully')
                    except APIException as inst:
                        if 401 <= inst.response_code <= 403:
                            logger.error("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                        if DEBUG:
                            logger.info(f"Error while updating company, with status code: {str(inst.response_code)}")
                else:
                    logger.info('To update a company, a company_id field is required')

            elif isinstance(company_profile, CompanyModel):
                if company_profile.company_id is not None:
                    try:
                        api_client.update_company(company_profile)
                        if DEBUG:
                            logger.info('Company Profile updated successfully')
                    except APIException as inst:
                        if 401 <= inst.response_code <= 403:
                            logger.error("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                        if DEBUG:
                            logger.info(f"Error while updating company, with status code: {str(inst.response_code)}")
                else:
                    logger.info('To update a company, a company_id field is required')
            else:
                try:
                    company_profile_json = APIHelper.json_deserialize(company_profile)
                    if 'company_id' in company_profile_json:
                        try:
                            api_client.update_company(CompanyModel.from_dictionary(company_profile_json))
                            if DEBUG:
                                logger.info('Company Profile updated successfully')
                        except APIException as inst:
                            if 401 <= inst.response_code <= 403:
                                logger.error("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                            if DEBUG:
                                logger.info(f"Error while updating company, with status code: {str(inst.response_code)}")
                    else:
                        logger.info('To update a company, a company_id field is required')
                except:
                    logger.warning('Error while deserializing the json, please make sure the json is valid')

    @classmethod
    def update_companies_batch(cls, companies_profiles, api_client, DEBUG):
        if not companies_profiles:
            logger.info('Expecting the input to be either of the type - List of CompanyModel, dict or json while updating users')
        else:
            if all(isinstance(company, dict) for company in companies_profiles):
                if all('company_id' in company for company in companies_profiles):
                    try:
                        batch_profiles = [CompanyModel.from_dictionary(d) for d in companies_profiles]
                        api_client.update_companies_batch(batch_profiles)
                        if DEBUG:
                            logger.info('Companies Profile updated successfully')
                    except APIException as inst:
                        if 401 <= inst.response_code <= 403:
                            logger.error("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                        if DEBUG:
                            logger.info(f"Error while updating companies, with status code: {str(inst.response_code)}")
                else:
                    logger.info('To update companies, an company_id field is required')

            elif all(isinstance(company, CompanyModel) for company in companies_profiles):
                if all(company.company_id is not None for company in companies_profiles):
                    try:
                        api_client.update_companies_batch(companies_profiles)
                        if DEBUG:
                            logger.info('Companies Profile updated successfully')
                    except APIException as inst:
                        if 401 <= inst.response_code <= 403:
                            logger.error("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                        if DEBUG:
                            logger.info(f"Error while updating companues, with status code: {str(inst.response_code)}")
                else:
                    logger.info('To update companies, a company_id field is required')
            else:
                try:
                    company_profiles_json = [APIHelper.json_deserialize(d) for d in companies_profiles]
                    if all(isinstance(company, dict) for company in company_profiles_json) and all(
                                    'company_id' in company for company in company_profiles_json):
                        try:
                            batch_profiles = [CompanyModel.from_dictionary(d) for d in company_profiles_json]
                            api_client.update_companies_batch(batch_profiles)
                            if DEBUG:
                                logger.info('Companies Profile updated successfully')
                        except APIException as inst:
                            if 401 <= inst.response_code <= 403:
                                logger.error("Unauthorized access sending event to Moesif. Please check your Appplication Id.")
                            if DEBUG:
                                logger.info(f"Error while updating companies, with status code: {str(inst.response_code)}")
                    else:
                        logger.info('To update companies, an company_id field is required')
                except:
                    logger.warning('Error while deserializing the json, please make sure the json is valid')
