moesifdjango Middleware for Python Django
========================

[Source Code on GitHub](https://github.com/moesif/moesifdjango)

__Check out Moesif's
[Python developer documentation](https://www.moesif.com/developer-documentation) to learn more__

(Documentation access requires an active account)

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
}
```

1. `APPLICATION_ID` (required) is obtained via your Moesif Account, this is required.
2. `REQUEST_HEADER_MASKS` (optional) is a list of strings for headers that you want to hide from Moesif.
3. `REQUEST_BODY_MASKS` (optional) is a list of key values in the body that you want to hide from Moesif. All key values in the body will be recursively removed before sending to Moesif.
4. `RESPONSE_HEADER_MASKS` (optional) performs the same function for response headers.
5. `RESPONSE_BODY_MASKS` (optional) performs the same task for response body.

How to run the test:
====================

  1. Manually clone the git repo
  2. Install moesifdjango middleware as in directions above.
  2. Copy `test.py` to your local directory for tests.
  3. Invoke `python manage.py test.`
