#!/usr/bin/env python

from distutils.core import setup

setup(name='Boompy',
      version='0.0.3',
      description='Boomi api client',
      author='Cullen MacDonald',
      author_email='cullen@handshake.com',
      packages=['boompy'],
      install_requires=["requests"],
)
