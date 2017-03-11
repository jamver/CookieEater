#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import os
import re

root = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(root, "cookie_eater", "__init__.py"), "r") as cf:
    reuse_content = cf.read()

attrs = dict(re.findall(r"__([a-z]+)__ *= *['\"](.+)['\"]", reuse_content))

with open("README.rst", "r") as readme_file:
    long_description = readme_file.read()

packages = ['cookie_eater', 'test']

setup(
    name='cookie-eater',
    version=attrs['version'],
    url='https://github.com/cdgriffith/CookieEater',
    license='MIT',
    author=attrs['author'],
    tests_require=["pytest", "coverage >= 3.6", "tox",  "pytest-cov",
                   "reusables"],
    install_requires=["reusables"],
    author_email='chris@cdgriffith.com',
    description='Browser Cookie Management',
    long_description=long_description,
    packages=packages,
    include_package_data=True,
    platforms='any',
    setup_requires=['pytest-runner'],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Utilities',
        'Topic :: Documentation :: Sphinx',
        ],
    extras_require={
        'testing': ["pytest", "coverage >= 3.6", "tox",  "pytest-cov",
                    "reusables"],
        },
)
