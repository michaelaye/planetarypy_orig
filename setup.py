# import ez_setup
# ez_setup.use_setuptools()
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

pandas_version = '0.16.0'

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['-v', '-m']
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name = "planetpy",
    version = "0.1",
    packages = find_packages(),

    install_requires = ['pandas'],
    # tests_require = ['pytest'],

    cmdclass = {'test': PyTest},


    #metadata
    author = "K.-Michael Aye",
    author_email = "michael.aye@lasp.colorado.edu",
    description = "Software tools for planetary science.",
    license = "BSD 3-clause",
    keywords = "planetary science",
    url = "http://lasp.colorado.edu",
)
