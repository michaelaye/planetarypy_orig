
#!/usr/bin/env python
# -*- coding: utf-8 -*-

pandas_version = '0.16.1'

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'pandas>='+pandas_version,
    'lxml',
    'html5lib',
    'beautifulsoup4'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='planetpy',
    version='0.1.0',
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
    license="BSD",
    zip_safe=False,
    keywords='planetpy',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Users',
        'License :: OSI Approved :: ISC License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    # test_suite='tests',
    # tests_require=test_requirements
)
