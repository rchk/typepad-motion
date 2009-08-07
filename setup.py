#!/usr/bin/env python
from setuptools import setup, find_packages
setup(
    name='motion',
    version='1.1',
    description='Community microblogging in the TypePad cloud',
    author='Six Apart',
    author_email='python@sixapart.com',
    url='http://code.sixapart.com/svn/motion/',

    packages=find_packages(),
    provides=['motion'],
    include_package_data=True,
    zip_safe=False,
    requires=['Django(>=1.0.2)', 'typepadapp'],
)
