import os, sys
from setuptools import Command, setup

long_description = open('README.md').read()

setup(
    author = 'Iwan Budi Kusnanto',
    url = 'https://github.com/iwanbk/nyamuk',
    author_email ='iwan.b.kusnanto@gmail.com',
    version ='0.2.0',
    install_requires = [],
    packages = ['nyamuk'],
    name = 'nyamuk',
    description = 'Python MQTT Client Library',
    long_description = long_description,
    license = "BSD",
    data_files = [
        ('doc/examples', ['test/pubnya.py', 'test/subnya.py',
                          'test/simple_publish.py', 'test/simple_subscribe.py']),
        ('doc', ['README.md'])
    ],
)
