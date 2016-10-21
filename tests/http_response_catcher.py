# -*- coding: utf-8 -*-

"""
    tests.http_response_catcher


"""

from moesifapi.http.http_call_back import *

class HttpResponseCatcher(HttpCallBack):

    """A class used for catching the HttpResponse object from controllers.
    
    This class inherits HttpCallBack and implements the on_after_response
    method to catch the HttpResponse object as returned by the HttpClient
    after a request is executed.

    """
    def on_before_request(self, request):
        pass;

    def on_after_response(self, context):
        self.response = context.response



