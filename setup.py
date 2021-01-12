#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license. 
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

from setuptools import setup, find_packages

version = '1.0'

with open("README.rst", 'r') as fin:
    README = fin.read()


setup(name='argusclient',
      version=version,
      description="Minimal client library for Argus webservice REST API",
      long_description=README,
      long_description_content_type="text/x-rst",
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Programming Language :: Python :: 2.7",
          "License :: OSI Approved :: BSD License",
          "Intended Audience :: Developers",
          "Topic :: System :: Monitoring",
      ],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='argus',
      author='Hari Krishna Dara',
      author_email='hdara@salesforce.com',
      url='https://github.com/SalesforceEng/argusclient',
      license="BSD-3-Clause",
      packages=find_packages(exclude=['ez_setup', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          "requests>=2.9.1",
          "lxml>=3.2.3"
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
