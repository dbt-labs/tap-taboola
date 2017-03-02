#!/usr/bin/env python

from setuptools import setup, find_packages
import os.path

setup(name='tap-taboola',
      version='0.0.1',
      description='Singer.io tap for extracting data from the Taboola API',
      author='Fishtown Analytics',
      url='http://fishtownanalytics.com',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      py_modules=['tap_taboola'],
      install_requires=[
          'singer-python==0.2.1',
          'backoff==1.3.2',
          'requests==2.12.4',
          'python-dateutil==2.6.0'
      ],
      entry_points='''
          [console_scripts]
          tap-taboola=tap_taboola:main
      ''',
      packages=['tap_taboola']
)
