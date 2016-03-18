#!/usr/bin/env python

from setuptools import setup
import sys, glob, os

req_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
requirements = [line for line in open(req_file) if line]

setup(
    name='r53-dyndns' ,
    version='0.1.1' ,
    author='Jay Deiman' ,
    author_email='admin@splitstreams.com' ,
    url='https://github.com/crustymonkey/r53-dyndns' ,
    description='Route53 dynamic DNS agent' ,
    long_description='Dynamic DNS agent which uses Amazon\'s '
        'Route53 and your own domain as the dns host.' ,
    scripts=['r53-dyndns.py'] ,
    data_files=[ ('etc' , glob.glob('etc/*')) ] ,
    packages=['libr53dyndns'] ,
    install_requires=requirements,
    classifiers=[
        'Development Status :: 4 - Beta' ,
        'Environment :: Console' ,
        'Intended Audience :: System Administrators' ,
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)' ,
        'Natural Language :: English' ,
        'Topic :: Internet :: Name Service (DNS)' ,
        'Operating System :: POSIX' ,
        'Programming Language :: Python' ,
        'Topic :: System :: Systems Administration' ,
    ]
)
