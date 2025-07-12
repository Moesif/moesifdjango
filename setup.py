# -*- coding: utf-8 -*-

"""
    setup module.
    See:
        https://packaging.python.org/en/latest/distributing.html
        https://github.com/pypa/sampleproject

"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
long_description = ''
if path.exists('README.md'):
    with open(path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='moesifdjango',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='2.3.13',

    description='Moesif Middleware for Python Django',
    long_description=long_description,
    long_description_content_type="text/markdown",

    # The project's main homepage.
    url='https://www.moesif.com/docs/server-integration/django/',

    # Author details
    author='Moesif, Inc',
    author_email='derric@moesif.com',

    license='Apache Software License',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Internet :: Log Analysis',
        'Topic :: Software Development :: Debuggers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Internet :: WWW/HTTP',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: Apache Software License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='log analysis restful api development debug',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['requests', 'jsonpickle', 'python-dateutil', 'isodatetimehandler', 'moesifapi>=1.5.3',
                      'moesifpythonrequest>=0.3.5', 'apscheduler', 'nose'
                      ],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': [],
        'test': ['nose'],
    },

)
