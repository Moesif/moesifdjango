# Moesif Middleware for Python Django

[![Built For][ico-built-for]][link-built-for]
[![Latest Version][ico-version]][link-package]
[![Language Versions][ico-language]][link-language]
[![Software License][ico-license]][link-license]
[![Source Code][ico-source]][link-source]

Django middleware to log _incoming_ API calls hitting your own service or _outgoing_ API calls 
going out to third parties and sends to [Moesif](https://www.moesif.com) for API analytics and monitoring 

[Source Code on GitHub](https://github.com/moesif/moesifdjango)

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
    'APPLICATION_ID': 'Your Moesif Application Id',
    'LOG_BODY': True,
    ...
    # For other options see below.
}
```

Your Moesif Application Id can be found in the [_Moesif Portal_](https://www.moesif.com/).
After signing up for a Moesif account, your Moesif Application Id will be displayed during the onboarding steps. 

You can always find your Moesif Application Id at any time by logging 
into the [_Moesif Portal_](https://www.moesif.com/), click on the top right menu,
and then clicking _API Keys_.

## Configuration options

#### __`APPLICATION_ID`__
(__required__), _string_, is obtained via your Moesif Account, this is required.

### Options specific to incoming API calls 

#### __`SKIP`__
(optional) _(request, response) => boolean_, a function that takes a request and a response, and returns true if you want to skip this particular event.

#### __`IDENTIFY_USER`__
(optional) _(request, response) => string_, a function that takes a request and a response, and returns a string that is the user id used by your system. While Moesif identify users automatically, and this middleware try to use the standard Django request.user.username, if your set up is very different from the standard implementations, it would be helpful to provide this function.

#### __`IDENTIFY_COMPANY`__
(optional) _(request, response) => string_, a function that takes a request and a response, and returns a string that is the company id for this event.

#### __`GET_SESSION_TOKEN`__
(optional) _(request, response) => string_, a function that takes a request and a response, and returns a string that is the session token for this event. Again, Moesif tries to get the session token automatically, but if you setup is very different from standard, this function will be very help for tying events together, and help you replay the events.

#### __`GET_METADATA`__
(optional) _(request, response) => dictionary_, getMetadata is a function that returns an object that allows you
to add custom metadata that will be associated with the event. The metadata must be a dictionary that can be converted to JSON. For example, you may want to save a VM instance_id, a trace_id, or a tenant_id with the request.

#### __`LOG_BODY`__
(optional) _boolean_, default True, Set to False to remove the HTTP body before sending to Moesif. If you want more control over which fields are included or not included look at the individual mask method below. 

#### __`MASK_EVENT_MODEL`__
(optional) _(EventModel) => EventModel_, a function that takes an EventModel and returns an EventModel with desired data removed. Use this if you prefer to write your own mask function than use the string based filter options: REQUEST_BODY_MASKS, REQUEST_HEADER_MASKS, RESPONSE_BODY_MASKS, & RESPONSE_HEADER_MASKS. The return value must be a valid EventModel required by Moesif data ingestion API. For details regarding EventModel please see the [Moesif Python API Documentation](https://www.moesif.com/docs/api?python).

#### __`BATCH_SIZE`__
(optional) __int__, default 25, Maximum batch size when sending to Moesif.

#### __`EVENT_QUEUE_SIZE`__
(optional) __int__, default 10000, Maximum number of events to hold in queue before sending to Moesif. In case of network issues when not able to connect/send event to Moesif, skips adding new to event to queue to prevent memory overflow.

#### __`AUTHORIZATION_HEADER_NAME`__
(optional) _string_, A request header field name used to identify the User in Moesif. Default value is `authorization`. Also, supports a comma separated string. We will check headers in order like `"X-Api-Key,Authorization"`.

#### __`AUTHORIZATION_USER_ID_FIELD`__
(optional) _string_, A field name used to parse the User from authorization header in Moesif. Default value is `sub`.

### Options specific to outgoing API calls 

The options below are applicable to outgoing API calls (calls you initiate using the Python [Requests](http://docs.python-requests.org/en/master/) lib to third parties like Stripe or to your own services.

For options that use the request and response as input arguments, these use the [Requests](http://docs.python-requests.org/en/master/api/) lib's request or response objects.

If you are not using Django, you can import the [moesifpythonrequest](https://github.com/Moesif/moesifpythonrequest) directly.

#### __`CAPTURE_OUTGOING_REQUESTS`__
_boolean_, Default False. Set to True to capture all outgoing API calls. False will disable this functionality. 

##### __`GET_METADATA_OUTGOING`__
(optional) _(req, res) => dictionary_, a function that enables you to return custom metadata associated with the logged API calls. 
Takes in the [Requests](http://docs.python-requests.org/en/master/api/) request and response object as arguments. You should implement a function that 
returns a dictionary containing your custom metadata. (must be able to be encoded into JSON). For example, you may want to save a VM instance_id, a trace_id, or a resource_id with the request.

##### __`SKIP_OUTGOING`__
(optional) _(req, res) => boolean_, a function that takes a [Requests](http://docs.python-requests.org/en/master/api/) request and response,
and returns true if you want to skip this particular event.

##### __`IDENTIFY_USER_OUTGOING`__
(optional, but highly recommended) _(req, res) => string_, a function that takes [Requests](http://docs.python-requests.org/en/master/api/) request and response, and returns a string that is the user id used by your system. While Moesif tries to identify users automatically,
but different frameworks and your implementation might be very different, it would be helpful and much more accurate to provide this function.

##### __`IDENTIFY_COMPANY_OUTGOING`__
(optional) _(req, res) => string_, a function that takes [Requests](http://docs.python-requests.org/en/master/api/) request and response, and returns a string that is the company id for this event.

##### __`GET_SESSION_TOKEN_OUTGOING`__
(optional) _(req, res) => string_, a function that takes [Requests](http://docs.python-requests.org/en/master/api/) request and response, and returns a string that is the session token for this event. Again, Moesif tries to get the session token automatically, but if you setup is very different from standard, this function will be very help for tying events together, and help you replay the events.

### General options
##### __`LOG_BODY_OUTGOING`__
(optional) _boolean_, default True, Set to False to remove logging request and response body.

#### __`LOCAL_DEBUG`__
_boolean_, set to True to print internal log messages for debugging SDK integration issues.

## Example 

A more detailed example is available at [https://github.com/Moesif/moesifdjangoexample](https://github.com/Moesif/moesifdjangoexample)

```python
def identify_user(req, res):
    # Your custom code that returns a user id string
    if req.user and req.user.is_authenticated:
        return req.user.username
    else:
        return None

def identify_company(req, res):
    # Your custom code that returns a company id string
    return "67890"

def should_skip(req, res):
    # Your custom code that returns true to skip logging
    return "health/probe" in req.path

def get_token(req, res):
    # If you don't want to use the standard Django session token,
    # add your custom code that returns a string for session/API token
    return "XXXXXXXXXXXXXX"

def mask_event(eventmodel):
    # Your custom code to change or remove any sensitive fields
    if 'password' in eventmodel.response.body:
        eventmodel.response.body['password'] = None
    return eventmodel

def get_metadata(req, res):
    return {
        'datacenter': 'westus',
        'deployment_version': 'v1.2.3',
    }


MOESIF_MIDDLEWARE = {
    'APPLICATION_ID': 'Your application id',
    'LOCAL_DEBUG': False,
    'LOG_BODY': True,
    'IDENTIFY_USER': identify_user,
    'IDENTIFY_COMPANY': identify_company,
    'GET_SESSION_TOKEN': get_token,
    'SKIP': should_skip,
    'MASK_EVENT_MODEL': mask_event,
    'GET_METADATA': get_metadata,
}

```

## Update User

### Update A Single User
Create or update a user profile in Moesif.
The metadata field can be any customer demographic or other info you want to store.
Only the `user_id` field is required.
This method is a convenient helper that calls the Moesif API lib.
For details, visit the [Python API Reference](https://www.moesif.com/docs/api?python#update-a-user).

```python
middleware = MoesifMiddleware(None)

# Only user_id is required.
# Campaign object is optional, but useful if you want to track ROI of acquisition channels
# See https://www.moesif.com/docs/api#users for campaign schema
# metadata can be any custom object
user = {
  'user_id': '12345',
  'company_id': '67890', # If set, associate user with a company object
  'campaign': {
    'utm_source': 'google',
    'utm_medium': 'cpc', 
    'utm_campaign': 'adwords',
    'utm_term': 'api+tooling',
    'utm_content': 'landing'
  },
  'metadata': {
    'email': 'john@acmeinc.com',
    'first_name': 'John',
    'last_name': 'Doe',
    'title': 'Software Engineer',
    'sales_info': {
        'stage': 'Customer',
        'lifetime_value': 24000,
        'account_owner': 'mary@contoso.com'
    },
  }
}

update_user = middleware.update_user(user)
```

### Update Users in Batch
Similar to update_user, but used to update a list of users in one batch. 
Only the `user_id` field is required.
This method is a convenient helper that calls the Moesif API lib.
For details, visit the [Python API Reference](https://www.moesif.com/docs/api?python#update-users-in-batch).

```python
middleware = MoesifMiddleware(None)

userA = {
  'user_id': '12345',
  'company_id': '67890', # If set, associate user with a company object
  'metadata': {
    'email': 'john@acmeinc.com',
    'first_name': 'John',
    'last_name': 'Doe',
    'title': 'Software Engineer',
    'sales_info': {
        'stage': 'Customer',
        'lifetime_value': 24000,
        'account_owner': 'mary@contoso.com'
    },
  }
}

userB = {
  'user_id': '54321',
  'company_id': '67890', # If set, associate user with a company object
  'metadata': {
    'email': 'mary@acmeinc.com',
    'first_name': 'Mary',
    'last_name': 'Jane',
    'title': 'Software Engineer',
    'sales_info': {
        'stage': 'Customer',
        'lifetime_value': 48000,
        'account_owner': 'mary@contoso.com'
    },
  }
}
update_users = middleware.update_users_batch([userA, userB])
```

## Update Company

### Update A Single Company
Create or update a company profile in Moesif.
The metadata field can be any company demographic or other info you want to store.
Only the `company_id` field is required.
This method is a convenient helper that calls the Moesif API lib.
For details, visit the [Python API Reference](https://www.moesif.com/docs/api?python#update-a-company).

```python
middleware = MoesifMiddleware(None)

# Only company_id is required.
# Campaign object is optional, but useful if you want to track ROI of acquisition channels
# See https://www.moesif.com/docs/api#update-a-company for campaign schema
# metadata can be any custom object
company = {
  'company_id': '67890',
  'company_domain': 'acmeinc.com', # If domain is set, Moesif will enrich your profiles with publicly available info 
  'campaign': {
    'utm_source': 'google',
    'utm_medium': 'cpc', 
    'utm_campaign': 'adwords',
    'utm_term': 'api+tooling',
    'utm_content': 'landing'
  },
  'metadata': {
    'org_name': 'Acme, Inc',
    'plan_name': 'Free',
    'deal_stage': 'Lead',
    'mrr': 24000,
    'demographics': {
        'alexa_ranking': 500000,
        'employee_count': 47
    },
  }
}

update_company = middleware.update_company(company)
```

### Update Companies in Batch
Similar to update_company, but used to update a list of companies in one batch. 
Only the `company_id` field is required.
This method is a convenient helper that calls the Moesif API lib.
For details, visit the [Python API Reference](https://www.moesif.com/docs/api?python#update-companies-in-batch).

```python
middleware = MoesifMiddleware(None)

companyA = {
  'company_id': '67890',
  'company_domain': 'acmeinc.com', # If domain is set, Moesif will enrich your profiles with publicly available info 
  'metadata': {
    'org_name': 'Acme, Inc',
    'plan_name': 'Free',
    'deal_stage': 'Lead',
    'mrr': 24000,
    'demographics': {
        'alexa_ranking': 500000,
        'employee_count': 47
    },
  }
}

companyB = {
  'company_id': '09876',
  'company_domain': 'contoso.com', # If domain is set, Moesif will enrich your profiles with publicly available info 
  'metadata': {
    'org_name': 'Contoso, Inc',
    'plan_name': 'Free',
    'deal_stage': 'Lead',
    'mrr': 48000,
    'demographics': {
        'alexa_ranking': 500000,
        'employee_count': 53
    },
  }
}

update_companies = middleware.update_companies_batch([userA, userB])
```

## Tested versions

Moesif has validated moesifdjango against the following combinations.  

| Python       | Django  | 
| ------------ | ------- | 
| Python 2.7   | 1.11.22 | 
| Python 2.7   | 1.11.22 | 
| Python 2.7   | 1.9     | 
| Python 3.4.5 | 1.11.22 | 
| Python 3.4.5 | 1.11.22 | 
| Python 3.4.5 | 1.9     | 
| Python 3.6.4 | 1.11.22 | 
| Python 3.6.4 | 1.11.22 | 
| Python 3.6.4 | 1.9     | 

## How to test

1. Manually clone the git repo
2. Invoke `pip install Django` if you haven't done so.
3. Invoke `pip install moesifdjango`
3. Add your own application id to 'tests/settings.py'. You can find your Application Id from [_Moesif Dashboard_](https://www.moesif.com/) -> _Top Right Menu_ -> _API Keys_
4. From terminal/cmd navigate to the root directory of the middleware tests.
5. Invoke `python manage.py test` if you are using Django 1.10 or newer.
6. Invoke `python manage.py test middleware_pre19_tests` if you are using Django 1.9 or older.

## Example

An example Moesif integration based on quick start tutorials of Django and Django Rest Framework:
[Moesif Django Example](https://github.com/Moesif/moesifdjangoexample)

## Other integrations

To view more documentation on integration options, please visit __[the Integration Options Documentation](https://www.moesif.com/docs/getting-started/integration-options/).__

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
