#! /usr/bin/env python
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import re
import os
import sys
from setuptools import setup, Command
import ConfigParser
import unittest

requires = ['boto']


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class SQLiteTest(Command):
    """
    Run the tests on SQLite
    """
    description = "Run tests on SQLite"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if self.distribution.tests_require:
            self.distribution.fetch_build_eggs(self.distribution.tests_require)

        os.environ['TRYTOND_DATABASE_URI'] = 'sqlite://'
        os.environ['DB_NAME'] = ':memory:'

        from tests import suite
        test_result = unittest.TextTestRunner(verbosity=3).run(suite())

        if test_result.wasSuccessful():
            sys.exit(0)
        sys.exit(-1)


config = ConfigParser.ConfigParser()
config.readfp(open('tryton.cfg'))
info = dict(config.items('tryton'))
for key in ('depends', 'extras_depend', 'xml'):
    if key in info:
        info[key] = info[key].strip().splitlines()
major_version, minor_version, _ = info.get('version', '0.0.1').split('.', 2)
major_version = int(major_version)
minor_version = int(minor_version)

for dep in info.get('depends', []):
    if not re.match(r'(ir|res|webdav)(\W|$)', dep):
        requires.append(
            'trytond_%s >= %s.%s, < %s.%s' % (
                dep, major_version, minor_version,
                major_version, minor_version + 1,
            )
        )
requires.append(
    'trytond >= %s.%s, < %s.%s' % (
        major_version, minor_version, major_version, minor_version + 1
    )
)

setup(
    name='trytond_attachment_s3',
    version=info.get('version', '0.0.1'),
    description='Amazon S3 backend for Tryton Attachments',
    long_description=read('README.md'),
    author='Openlabs Technologies & Consulting (P) Limited',
    author_email=info.get('email', ''),
    url='https://github.com/openlabs/trytond-attachment-s3',
    package_dir={'trytond.modules.attachment_s3': '.'},
    packages=[
        'trytond.modules.attachment_s3',
        'trytond.modules.attachment_s3.tests',
    ],
    package_data={
        'trytond.modules.attachment_s3': info.get('xml', []) + [
            'tryton.cfg', 'locale/*.po', '*.odt', 'icons/*.svg'
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    license='BSD',
    install_requires=requires,
    zip_safe=False,
    entry_points="""
    [trytond.modules]
    attachment_s3 = trytond.modules.attachment_s3
    """,
    test_suite='tests',
    test_loader='trytond.test_loader:Loader',
    cmdclass={
        'test': SQLiteTest,
    },
)
