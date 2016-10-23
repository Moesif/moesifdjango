moesifdjango Middleware for Python Django
========================

[Source Code on GitHub](https://github.com/moesif/moesif-django)

This middleware automatically logs api_calls to moesif for analysis and monitoring.

__Check out Moesif's
[Python developer documentation](https://www.moesif.com/developer-documentation) to learn more__

(Documentation access requires an active account)

How to install:
===============

```shell
pip install moesifdjango
```

How to setup:
===========

In your `settings.py` file in your Django project directory, please add `moesifdjango.middleware.moesif_middleware`
to the MIDDLEWARE array.

Because of middleware execution order, it is best to add moesifdjango middleware after SessionMiddleware
and AuthenticationMiddleware, because those middleware adds very useful data for error analysis. But to capture the entire response data,
add moesifdjango middleware before any middleware that might modify the response.

```
MIDDLEWARE = [
    ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'moesifdjango.middleware.moesif_middleware',
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
}
```

1. `APPLICATION_ID` (required) is obtained via your Moesif Account, this is required.
2. `REQUEST_HEADER_MASKS` (optional) is a list of strings for headers that you want to hide from Moesif.
3. `REQUEST_BODY_MASKS` (optional) is a list of key values in the body that you want to hide from Moesif. All key values in the body will be recursively removed before sending to Moesif.
4. `RESPONSE_HEADER_MASKS` (optional) performs the same function for response headers.
5. `RESPONSE_BODY_MASKS` (optional) performs the same task for response body.

How  to test:
=============
You can test the SDK with automatically generated test
cases. unittest is used as the testing framework and nose is used as the test
runner. You can run the tests as follows:

  1. Manually clone the git repo
  2. Install moesifdjango middleware as in directions above.
  2. Copy `test.py` to your local directory for tests.
  3. Invoke `python manage.py test.`
