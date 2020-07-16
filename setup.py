#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import setuptools
from emzero import __version__

with open('README.md') as fh:
    long_description = fh.read()

setuptools.setup(
    name='emzero',
    version=__version__,
    author='vadno',  # Will warn about missing e-mail
    description='A module for marking zero pronouns in dependency parsed sentences',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/vadno/emzero',
    # license='GNU Lesser General Public License v3 (LGPLv3)',  # Never really used in favour of classifiers
    # platforms='any',  # Never really used in favour of classifiers
    packages=setuptools.find_packages(exclude=['tests']),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: POSIX :: Linux',
    ],
    python_requires='>=3.6',
    install_requires=['xtsv>=1.0,<2.0',  # TODO: List dependencies at only one file requirements.txt vs. setup.py
                      ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'emzero=emzero.__main__:main',
        ]
    },
)
