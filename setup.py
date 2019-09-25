#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='tap-slack',
      version='0.0.1',
      description='Singer.io tap for extracting data from the Slack API',
      author='Fishtown Analytics',
      url='http://fishtownanalytics.com',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      py_modules=['tap_slack'],
      install_requires=[
          'tap-framework==0.0.4',
          'slackclient',
      ],
      entry_points='''
          [console_scripts]
          tap-slack=tap_slack:main
      ''',
      packages=find_packages(),
      package_data={
          'tap_slack': [
              'schemas/*.json'
          ]
      })
