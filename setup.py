from __future__ import print_function

import sys
import os

python_version = sys.version_info[:2]

assert python_version in ((2, 6), (2, 7)) or python_version >= (3, 3), \
        'The New Relic Python agent only supports Python 2.6, 2.7 and 3.3+.'

with_setuptools = False

try:
    from setuptools import setup
    with_setuptools = True
except ImportError:
    from distutils.core import setup

from distutils.core import Extension
from distutils.command.build_ext import build_ext
from distutils.errors import (CCompilerError, DistutilsExecError,
        DistutilsPlatformError)

copyright = '(C) Copyright 2010-2014 New Relic Inc. All rights reserved.'

script_directory = os.path.dirname(__file__)
if not script_directory:
    script_directory = os.getcwd()

develop_file = os.path.join(script_directory, 'DEVELOP')
version_file = os.path.join(script_directory, 'VERSION')
license_file = os.path.join(script_directory, 'LICENSE')

if os.path.exists(develop_file):
    # Building from source repository.

    import newrelic

    package_version = newrelic.version

    version_file_fds = open(version_file, 'w')
    print(package_version, file=version_file_fds)
    version_file_fds.close()

else:
    # Installing from release package.

    package_version = open(version_file, 'r').read().strip()

if sys.platform == 'win32' and python_version > (2, 6):
    build_ext_errors = (CCompilerError, DistutilsExecError,
            DistutilsPlatformError, IOError)
else:
    build_ext_errors = (CCompilerError, DistutilsExecError,
            DistutilsPlatformError)

class BuildExtFailed(Exception):
    pass

class optional_build_ext(build_ext):
    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            raise BuildExtFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except build_ext_errors:
            raise BuildExtFailed()

packages = [
  "newrelic",
  "newrelic.admin",
  "newrelic.api",
  "newrelic.bootstrap",
  "newrelic.common",
  "newrelic.core",
  "newrelic.extras",
  "newrelic.extras.framework_django",
  "newrelic.extras.framework_django.templatetags",
  "newrelic.hooks",
  "newrelic.hooks.framework_tornado",
  "newrelic.network",
  "newrelic/packages",
  "newrelic/packages/requests",
  "newrelic/packages/requests/packages",
  "newrelic/packages/requests/packages/charade",
  "newrelic/packages/requests/packages/urllib3",
  "newrelic/packages/requests/packages/urllib3/packages",
  "newrelic/packages/requests/packages/urllib3/packages/ssl_match_hostname",
  "newrelic/packages/wrapt",
  "newrelic.samplers",
]

kwargs = dict(
  name = "newrelic",
  version = package_version,
  description = "Python agent for New Relic",
  author = "New Relic",
  author_email = "support@newrelic.com",
  license = copyright,
  url = "http://www.newrelic.com",
  packages = packages,
  package_data = { 'newrelic': ['newrelic.ini', 'LICENSE',
          'packages/requests/LICENSE', 'packages/requests/NOTICE',
          'packages/requests/cacert.pem'] },
  extra_path = ( "newrelic", "newrelic-%s" % package_version ),
  scripts = [ 'scripts/newrelic-admin' ],
)

if with_setuptools:
    kwargs['entry_points'] = {
            'console_scripts': ['newrelic-admin = newrelic.admin:main'],
            }

def run_setup(with_extensions):
    def _run_setup():
        kwargs_tmp = dict(kwargs)

        if with_extensions:
            monotonic_libraries = []
            if sys.platform == 'linux2':
                monotonic_libraries = ['rt']

            kwargs_tmp['ext_modules'] = [
                    Extension("newrelic.packages.wrapt._wrappers",
                        ["newrelic/packages/wrapt/_wrappers.c"]),
                    Extension("newrelic.common._monotonic",
                        ["newrelic/common/_monotonic.c"],
                        libraries=monotonic_libraries),
                    Extension("newrelic.core._thread_utilization",
                        ["newrelic/core/_thread_utilization.c"]),
                    ]
            kwargs_tmp['cmdclass'] = dict(build_ext=optional_build_ext)

        setup(**kwargs_tmp)

    if os.environ.get('TDDIUM') is not None:
        try:
            print('INFO: Running under tddium. Use lock.')
            from lock_file import LockFile
        except ImportError:
            print('ERROR: Cannot import locking mechanism.')
            _run_setup()
        else:
            print('INFO: Attempting to create lock file.')
            with LockFile('setup.lock', wait=True):
                _run_setup()
    else:
        _run_setup()

WARNING = """
WARNING: The optional C extension components of the Python agent could
not be compiled. This can occur where a compiler is not present on the
target system or the Python installation does not have the corresponding
developer package installed. The Python agent will instead be installed
without the extensions. The consequence of this is that although the
Python agent will still run, JSON encoding/decoding speedups will not be
available, nor will some of the non core features of the Python agent.
"""

with_extensions = os.environ.get('NEW_RELIC_EXTENSIONS', None)
if with_extensions:
    if with_extensions.lower() == 'true':
        with_extensions = True
    elif with_extensions.lower() == 'false':
        with_extensions = False
    else:
        with_extensions = None

if hasattr(sys, 'pypy_version_info'):
    with_extensions = False

if with_extensions is not None:
    run_setup(with_extensions=with_extensions)

else:
    try:
        run_setup(with_extensions=True)

    except BuildExtFailed:

        print(75 * '*')

        print(WARNING)
        print("INFO: Trying to build without extensions.")

        print()
        print(75 * '*')

        run_setup(with_extensions=False)

        print(75 * '*')

        print(WARNING)
        print("INFO: Only pure Python agent was installed.")

        print()
        print(75 * '*')
