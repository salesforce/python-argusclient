from setuptools import setup, find_packages

version = '0.2'

setup(name='argusclient',
      version=version,
      description="Minimal client library for Argus webservice REST API",
      long_description="""\
""",
      classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='argus',
      author='Hari Krishna Dara',
      author_email='hdara@salesforce.com',
      url='https://github.com/SalesforceEng/argusclient',
      license='',
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
