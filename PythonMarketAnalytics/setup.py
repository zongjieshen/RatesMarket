from distutils.core import setup

VERSION = '0.2'
LICENSE = 'MIT'

setup(
        name='Market',
        packages=['Market'],
        version=VERSION,
        license=LICENSE,
        install_requires=[
            'scipy',
            'numpy',
            'holidays',
            'dataclasses'
            ],
     )
