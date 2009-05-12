#!/usr/bin/env python
from distutils.core import setup
setup(
    name='motion',
    version='1.0',
    description='Community microblogging in the TypePad cloud',
    author='Six Apart',
    author_email='python@sixapart.com',
    url='http://code.sixapart.com/svn/motion/',

    packages=['motion'],
    provides=['motion'],
    requires=['Django(>=1.0.2)', 'typepadapp'],
)
