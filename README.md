Middleware for Python Django
============================

[Source Code on GitHub](https://github.com/moesif/moesifdjango)

__Check out Moesif's
[Python developer documentation](https://www.moesif.com/developer-documentation/?python) to learn more__

This SDK uses the Requests library and will work for Python 2.7 — 3.5.

How to install:
===============

```shell
pip install moesifdjango
```

How to setup:
=============

In your `settings.py` file in your Django project directory, please add `moesifdjango.middleware.moesif_middleware`
to the MIDDLEWARE array.

Because of middleware execution order, it is best to add moesifdjango middleware __below__ SessionMiddleware
and AuthenticationMiddleware, because they add useful session data that enables deeper error analysis. On the other hand, if you have other middleware that modified response before going out, you may choose to place Moesif middleware __above__ the middleware modifying response. This allows Moesif to see the modifications to the response data and see closer to what is going over the wire.

```
MIDDLEWARE = [
    ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'moesifdjango.middleware.moesif_middleware'
    ...
]
```

Add `MOESIF_MIDDLEWARE` to your settings file.

```
MOESIF_MIDDLEWARE = {
    'APPLICATION_ID': 'Your Application ID Found in Settings on Moesif',
    'REQUEST_HEADER_MASKS': ['header1', 'header2'],
    'REQUEST_BODY_MASKS': ['key1', 'key2'],
    'RESPONSE_HEADER_MASKS': ['header1', 'header2'],
    'RESPONSE_BODY_MASKS': ['key1', 'key2'],
    ...
}
```

1. `APPLICATION_ID` (__required__), _string_, is obtained via your Moesif Account, this is required.
2. `REQUEST_HEADER_MASKS` (optional), _string[]_, is a list of strings for headers that you want to hide from Moesif.
3. `REQUEST_BODY_MASKS` (optional), _string[]_, is a list of key values in the body that you want to hide from Moesif. All key values in the body will be recursively removed before sending to Moesif.
4. `RESPONSE_HEADER_MASKS` (optional), _string[]_, performs the same function for response headers.
5. `RESPONSE_BODY_MASKS` (optional), _string[]_, performs the same task for response body.
6. `SKIP` (optional) _(request, response) => boolean_, a function that takes a request and a response, and returns true if you want to skip this particular event.
7. `IDENTIFY_USER` (optional) _(request, response) => string_, a function that takes a request and a response, and returns a string that is the user id used by your system. While Moesif identify users automatically, and this middleware try to use the standard Django request.user.username, if your set up is very different from the standard implementations, it would be helpful to provide this function.
8. `GET_SESSION_TOKEN` (optional) _(request, response) => string_, a function that takes a request and a response, and returns a string that is the session token for this event. Again, Moesif tries to get the session token automatically, but if you setup is very different from standard, this function will be very help for tying events together, and help you replay the events.
9. `MASK_EVENT_MODEL` (optional) _(EventModel) => EventModel_, a function that takes an EventModel and returns an EventModel with desired data removed. Use this if you prefer to write your own mask function than use the string based filter options: REQUEST_BODY_MASKS, REQUEST_HEADER_MASKS, RESPONSE_BODY_MASKS, & RESPONSE_HEADER_MASKS. The return value must be a valid EventModel required by Moesif data ingestion API. For details regarding EventModel please see documentation for [moesifapi-python](https://github.com/Moesif/moesifapi-python).


How to run the test:
====================

  1. Manually clone the git repo
  2. Install moesifdjango middleware as in directions above.
  2. Copy `test.py` to your local directory for tests.
  3. Invoke `python manage.py test.`
