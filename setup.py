import os, sys
from setuptools import Command, setup

long_description = open('README').read()

setup(
    author = 'Iwan Budi Kusnanto',
    url = 'https://github.com/iwanbk/nyamuk',
    author_email ='iwan.b.kusnanto@gmail.com',
    version ='0.1.1',
    install_requires = [],
    packages = ['nyamuk'],
    name = 'nyamuk',
    description = 'Python MQTT Client Library',
    long_description = long_description,
    license = "BSD",
)
