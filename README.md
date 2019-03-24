# Moesif Middleware for Python Django

[![Built For][ico-built-for]][link-built-for]
[![Latest Version][ico-version]][link-package]
[![Language Versions][ico-language]][link-language]
[![Software License][ico-license]][link-license]
[![Source Code][ico-source]][link-source]

Django middleware to capture _incoming_ or _outgoing_ API calls and send to the Moesif API Analytics platform.

[Source Code on GitHub](https://github.com/moesif/moesifdjango)

This SDK uses the Requests library and will work for Python 2.7 — 3.5.

## How to install

```shell
pip install moesifdjango
```

## How to use

In your `settings.py` file in your Django project directory, please add `moesifdjango.middleware.moesif_middleware`
to the MIDDLEWARE array.
If you plan to use celery as the backend of asynchronous delivered logged requests, you also need to add `moesifdjango` to your `INSTALLED_APPS`.

Because of middleware execution order, it is best to add moesifdjango middleware __below__ SessionMiddleware
and AuthenticationMiddleware, because they add useful session data that enables deeper error analysis. On the other hand, if you have other middleware that modified response before going out, you may choose to place Moesif middleware __above__ the middleware modifying response. This allows Moesif to see the modifications to the response data and see closer to what is going over the wire.

### Changes in Django 1.10

Django middleware style and setup was refactored in version 1.10. You need need to import the correct version of Moesif middleware depending on your Django version. If you're using Django 1.10 or greater, use `moesifdjango.middleware.moesif_middleware`. However, if you're using Django 1.9 or older, you need to follow the legacy style for importing middleware and use `moesifdjango.middleware_pre19.MoesifMiddlewarePre19` instead.

You can find your current Django version via `python -c "import django; print(django.get_version())"`
{: .notice--info}

### Django 1.10 or newer

Add the middleware to your application:

Django 1.10 renamed `MIDDLEWARE_CLASSES` to `MIDDLEWARE.` If you're using 1.10 or newer and still using the legacy MIDDLEWARE_CLASSES,
the Moesif middleware will not run.
{: .notice--danger}

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

### Django 1.9 or older

Add the middleware to your application:

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


#### __`GET_METADATA`__
(optional) _(request, response) => dictionary_, getMetadata is a function that returns an object that allows you
to add custom metadata that will be associated with the event. The metadata must be a dictionary that can be converted to JSON. For example, you may want to save a VM instance_id, a trace_id, or a tenant_id with the request.

#### __`MASK_EVENT_MODEL`__
(optional) _(EventModel) => EventModel_, a function that takes an EventModel and returns an EventModel with desired data removed. Use this if you prefer to write your own mask function than use the string based filter options: REQUEST_BODY_MASKS, REQUEST_HEADER_MASKS, RESPONSE_BODY_MASKS, & RESPONSE_HEADER_MASKS. The return value must be a valid EventModel required by Moesif data ingestion API. For details regarding EventModel please see the [Moesif Python API Documentation](https://www.moesif.com/docs/api?python).

#### __`LOCAL_DEBUG`__
_boolean_, set to True to print internal log messages for debugging SDK integration issues.

#### __`USE_CELERY`__
_boolean_, Default False. Set to True to use Celery for queuing sending data to Moesif. Check out [Celery documentation](http://docs.celeryproject.org) for more info.

#### __`REQUEST_HEADER_MASKS`__
(deprecated), _string[]_, is a list of strings for headers that you want to hide from Moesif. Will be removed in future version. Replaced by the function based 'MASK_EVENT_MODEL' for additional flexibility.

#### __`REQUEST_BODY_MASKS`__
(deprecated), _string[]_, is a list of key values in the body that you want to hide from Moesif. All key values in the body will be recursively removed before sending to Moesif. Will be removed in future version. Replaced by the function based 'MASK_EVENT_MODEL' for additional flexibility.

#### __`RESPONSE_HEADER_MASKS`__
(deprecated), _string[]_, performs the same function for response headers. Will be removed in future version. Replaced by the function based 'MASK_EVENT_MODEL' for additional flexibility.

#### __`RESPONSE_BODY_MASKS`__
(deprecated), _string[]_, performs the same task for response body. Will be removed in future version. Replaced by the function based 'MASK_EVENT_MODEL' for additional flexibility.

#### __`CAPTURE_OUTGOING_REQUESTS`__
_boolean_, Default False. Set to True to capture all outgoing API calls from your app to third parties like Stripe or to your own dependencies while using [Requests](http://docs.python-requests.org/en/master/) library. The options below is applied to outgoing API calls.
When the request is outgoing, for options functions that take request and response as input arguments, the request and response objects passed in are [Requests](http://docs.python-requests.org/en/master/api/) request or response objects.

##### __`SKIP_OUTGOING`__
(optional) _(req, res) => boolean_, a function that takes a [Requests](http://docs.python-requests.org/en/master/api/) request and response,
and returns true if you want to skip this particular event.

##### __`IDENTIFY_USER_OUTGOING`__
(optional, but highly recommended) _(req, res) => string_, a function that takes [Requests](http://docs.python-requests.org/en/master/api/) request and response, and returns a string that is the user id used by your system. While Moesif tries to identify users automatically,
but different frameworks and your implementation might be very different, it would be helpful and much more accurate to provide this function.

##### __`GET_METADATA_OUTGOING`__
(optional) _(req, res) => dictionary_, a function that takes [Requests](http://docs.python-requests.org/en/master/api/) request and response, and
returns a dictionary (must be able to be encoded into JSON). This allows
to associate this event with custom metadata. For example, you may want to save a VM instance_id, a trace_id, or a tenant_id with the request.

##### __`GET_SESSION_TOKEN_OUTGOING`__
(optional) _(req, res) => string_, a function that takes [Requests](http://docs.python-requests.org/en/master/api/) request and response, and returns a string that is the session token for this event. Again, Moesif tries to get the session token automatically, but if you setup is very different from standard, this function will be very help for tying events together, and help you replay the events.

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

def get_metadata(req, res):
    return {
        'foo': '12345',
        'bar': '23456',
    }


MOESIF_MIDDLEWARE = {
    'APPLICATION_ID': 'Your application id',
    'LOCAL_DEBUG': False,
    'IDENTIFY_USER': identifyUser,
    'GET_SESSION_TOKEN': get_token,
    'SKIP': should_skip,
    'MASK_EVENT_MODEL': mask_event,
    'GET_METADATA': get_metadata,
    'USE_CELERY': False
}

```

## Update User

### update_user method
A method is attached to the moesif middleware object to update the users profile or metadata.
The metadata field can be any custom data you want to set on the user. The `user_id` field is required.

```python
middleware = MoesifMiddleware(None)
update_user = middleware.update_user({
    'user_id': 'testpythonapiuser',
    'session_token': 'jkj9324-23489y5324-ksndf8-d9syf8',
    'metadata': {'email': 'abc@email.com', 'name': 'abcde', 'image': '1234'}
    })
```

### update_users_batch method
A method is attached to the moesif middleware object to update the users profile or metadata in batch.
The metadata field can be any custom data you want to set on the user. The `user_id` field is required.

```python
middleware = MoesifMiddleware(None)
update_users = middleware.update_users_batch([{
        'user_id': 'testpythonapiuser',
        'metadata': {'email': 'abc@email.com', 'name': 'abcdefg', 'image': '123'}
    }, {
        'user_id': 'testpythonapiuser1',
        'metadata': {'email': 'abc@email.com', 'name': 'abcdefg', 'image': '123'}
    }])
```

## How to test

1. Manually clone the git repo
2. Invoke `pip install Django` if you haven't done so.
3. Invoke `pip install moesifdjango`
3. Add your own application id to 'tests/settings.py'. You can find your Application Id from [_Moesif Dashboard_](https://www.moesif.com/) -> _Top Right Menu_ -> _Installation_
4. From terminal/cmd navigate to the root directory of the middleware tests.
5. Invoke `python manage.py test` if you are using Django 1.10 or newer.
6. Invoke `python manage.py test middleware_pre19_tests` if you are using Django 1.9 or older.

## Example

An example Moesif integration based on quick start tutorials of Django and Django Rest Framework:
[Moesif Django Example](https://github.com/Moesif/moesifdjangoexample)

## Other integrations

To view more more documentation on integration options, please visit __[the Integration Options Documentation](https://www.moesif.com/docs/getting-started/integration-options/).__

[ico-built-for]: https://img.shields.io/badge/built%20for-django-blue.svg
[ico-version]: https://img.shields.io/pypi/v/moesifdjango.svg
[ico-language]: https://img.shields.io/pypi/pyversions/moesifdjango.svg
[ico-license]: https://img.shields.io/badge/License-Apache%202.0-green.svg
[ico-source]: https://img.shields.io/github/last-commit/moesif/moesifdjango.svg?style=social

[link-built-for]: https://www.djangoproject.com/
[link-package]: https://pypi.python.org/pypi/moesifdjango
[link-language]: https://pypi.python.org/pypi/moesifdjango
[link-license]: https://raw.githubusercontent.com/Moesif/moesifdjango/master/LICENSE
[link-source]: https://github.com/Moesif/moesifdjango
