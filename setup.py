#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import sys

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'pandas',
    'pvl',
    'tqdm',
    'click',
    'toml',
    'requests'
]
if sys.version_info < (3,7):
    requirements.append('importlib_resources')

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='planetpy',
    version='0.4.3',
    description="Python module to support analysis of planetary data.",
    long_description=readme + '\n\n' + history,
    author="K.-Michael Aye",
    author_email='kmichael.aye@gmail.com',
    url='https://github.com/michaelaye/planetpy',
    packages=[
        'planetpy',
    ],
    package_dir={'planetpy':
                 'planetpy'},
    include_package_data=True,
    install_requires=requirements,
    license="ISC",
    zip_safe=False,
    keywords='planetpy',
    entry_points={
        "console_scripts": [
            'nasa_date_to_iso = planetpy.utils:nasa_date_to_iso_command',
            'planetpy_indices = planetpy.pdstools.cli:greet',
        ]
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    # test_suite='tests',
    # tests_require=test_requirements
)
