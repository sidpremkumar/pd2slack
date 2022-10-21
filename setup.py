from setuptools import setup

with open('requirements.txt', 'rb') as f:
    install_requires = f.read().decode('utf-8').split('\n')

with open('README.md', 'rb') as f:
    long_description = f.read().decode('utf-8')

setup(
    name='pd2slack',
    version=0.51,
    description='Syncs PD On-call to Slack User Group',
    long_description = long_description,
    long_description_content_type='text/markdown',
    author='Sid Premkumar',
    author_email='sid.premkumar@gmail.com',
    url='https://github.com/sidpremkumar/pd2slack',
    install_requires=install_requires,
    packages=[
        'pd2slack',
    ],
    entry_points={
        'console_scripts': [
            'pd2slack=pd2slack.main:main',
        ],
    },
)
