# This file is part of sync2jira.
# Copyright (C) 2016 Red Hat, Inc.
#
# sync2jira is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
from setuptools import setup

with open('requirements.txt', 'rb') as f:
    install_requires = f.read().decode('utf-8').split('\n')

setup(
    name='pd2slack',
    version=1.0,
    description='Syncs PD On-call to Slack User Group',
    author='Sid Premkumar',
    author_email='sid.premkumar@gmail.com@redhat.com',
    # url='https://pagure.io/sync-to-jira', todo: update this Link
    install_requires=install_requires,
    packages=[
        'pd2slack',
    ],
    # include_package_data=True,
    # zip_safe=False,
    entry_points={
        'console_scripts': [
            'pd2slack=pd2slack.main:main',
        ],
    },
)