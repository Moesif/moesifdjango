# Moesif Middleware for Python Django

Django middleware to log _incoming_ REST API calls to Moesif's error analysis platform.

[Source Code on GitHub](https://github.com/moesif/moesifdjango)

[Package on PyPI](https://pypi.python.org/pypi/moesifdjango)

This SDK uses the Requests library and will work for Python 2.7 — 3.5.

## How to install

```shell
pip install moesifdjango
```

## How to use

In your `settings.py` file in your Django project directory, please add `moesifdjango.middleware.moesif_middleware`
to the MIDDLEWARE array.

Because of middleware execution order, it is best to add moesifdjango middleware __below__ SessionMiddleware
and AuthenticationMiddleware, because they add useful session data that enables deeper error analysis. On the other hand, if you have other middleware that modified response before going out, you may choose to place Moesif middleware __above__ the middleware modifying response. This allows Moesif to see the modifications to the response data and see closer to what is going over the wire.

Django middleware style and setup changed drastically from version 1.10.

For __Django 1.10 or newer__, the please add Middleware this way:

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

For __Django 1.9 or older__, please add Middleware this way:

```
MIDDLEWARE_CLASSES = [
    ...
    'moesifdjango.middleware_pre19.MoesifMiddlewarePre19',
    ...
    # other middlewares
]
```

Also, add `MOESIF_MIDDLEWARE` to your `settings.py` file,

```

MOESIF_MIDDLEWARE = {
    'APPLICATION_ID': 'Your Application ID Found in Settings on Moesif',
    ...
    # other options see below.
}
```

You can find your Application Id from [_Moesif Dashboard_](https://www.moesif.com/) -> _Top Right Menu_ -> _App Setup_

## Configuration options

#### __`APPLICATION_ID`__
(__required__), _string_, is obtained via your Moesif Account, this is required.

#### __`SKIP`__
(optional) _(request, response) => boolean_, a function that takes a request and a response, and returns true if you want to skip this particular event.

#### __`IDENTIFY_USER`__
(optional) _(request, response) => string_, a function that takes a request and a response, and returns a string that is the user id used by your system. While Moesif identify users automatically, and this middleware try to use the standard Django request.user.username, if your set up is very different from the standard implementations, it would be helpful to provide this function.

#### __`GET_SESSION_TOKEN`__
(optional) _(request, response) => string_, a function that takes a request and a response, and returns a string that is the session token for this event. Again, Moesif tries to get the session token automatically, but if you setup is very different from standard, this function will be very help for tying events together, and help you replay the events.

#### __`MASK_EVENT_MODEL`__
(optional) _(EventModel) => EventModel_, a function that takes an EventModel and returns an EventModel with desired data removed. Use this if you prefer to write your own mask function than use the string based filter options: REQUEST_BODY_MASKS, REQUEST_HEADER_MASKS, RESPONSE_BODY_MASKS, & RESPONSE_HEADER_MASKS. The return value must be a valid EventModel required by Moesif data ingestion API. For details regarding EventModel please see the [Moesif Python API Documentation](https://www.moesif.com/docs/api?python).

#### __`REQUEST_HEADER_MASKS`__
(deprecated), _string[]_, is a list of strings for headers that you want to hide from Moesif. Will be removed in future version. Replaced by the function based 'MASK_EVENT_MODEL' for additional flexibility.

#### __`REQUEST_BODY_MASKS`__
(deprecated), _string[]_, is a list of key values in the body that you want to hide from Moesif. All key values in the body will be recursively removed before sending to Moesif. Will be removed in future version. Replaced by the function based 'MASK_EVENT_MODEL' for additional flexibility.

#### __`RESPONSE_HEADER_MASKS`__
(deprecated), _string[]_, performs the same function for response headers. Will be removed in future version. Replaced by the function based 'MASK_EVENT_MODEL' for additional flexibility.

#### __`RESPONSE_BODY_MASKS`__
(deprecated), _string[]_, performs the same task for response body. Will be removed in future version. Replaced by the function based 'MASK_EVENT_MODEL' for additional flexibility.

### Example:

```python
def identifyUser(req, res):
    # if your setup do not use the standard request.user.username
    # return the user id here
    return "user_id_1"

def should_skip(req, res):
    if "healthprobe" in req.path:
        return True
    else:
        return False

def get_token(req, res):
    # if your setup do not use the standard Django method for
    # setting session tokens. do it here.
    return "token"

def mask_event(eventmodel):
    # do something to remove sensitive fields
    # be sure not to remove any required fields.
    return eventmodel

MOESIF_MIDDLEWARE = {
    'APPLICATION_ID': 'Your application id',
    'LOCAL_DEBUG': False,
    'IDENTIFY_USER': identifyUser,
    'GET_SESSION_TOKEN': get_token,
    'SKIP': should_skip,
    'MASK_EVENT_MODEL': mask_event,
}

```

## How to run tests

  1. Manually clone the git repo
  2. Install moesifdjango middleware as in directions above.
  2. Copy `test.py` to your local directory for tests.
  3. Invoke `python manage.py test.`


## Other integrations

To view more more documentation on integration options, please visit __[the Integration Options Documentation](https://www.moesif.com/docs/getting-started/integration-options/).__
