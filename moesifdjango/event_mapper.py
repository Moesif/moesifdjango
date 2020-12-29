from moesifapi.models import *


class EventMapper:

    def __init__(self):
        pass

    @classmethod
    def to_request(self, req_time, uri, method, api_version, ip_address, req_headers, req_body, transfer_encoding):
        return EventRequestModel(time=req_time,
                                 uri=uri,
                                 verb=method,
                                 api_version=api_version,
                                 ip_address=ip_address,
                                 headers=req_headers,
                                 body=req_body,
                                 transfer_encoding=transfer_encoding)

    @classmethod
    def to_response(self, rsp_time, status_code, rsp_headers, rsp_body, transfer_encoding):
        return EventResponseModel(time=rsp_time,
                                  status=status_code,
                                  headers=rsp_headers,
                                  body=rsp_body,
                                  transfer_encoding=transfer_encoding)

    @classmethod
    def to_event(cls, event_req, event_rsp, user_id, company_id, session_token, metadata):
        # Prepare Event Model
        return EventModel(request=event_req,
                          response=event_rsp,
                          user_id=user_id,
                          company_id=company_id,
                          session_token=session_token,
                          metadata=metadata,
                          direction="Incoming")
