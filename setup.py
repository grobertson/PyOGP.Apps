"""
@file setup.py
@date 2008-09-16
Contributors can be viewed at:
http://svn.secondlife.com/svn/linden/projects/2008/pyogp/CONTRIBUTORS.txt

$LicenseInfo:firstyear=2008&license=apachev2$

Copyright 2008, Linden Research, Inc.

Licensed under the Apache License, Version 2.0 (the "License").
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0
or in
http://svn.secondlife.com/svn/linden/projects/2008/pyogp/LICENSE.txt

$/LicenseInfo$
"""

from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='pyogp.apps',
     version=version,
     description="basic pyogp apps package",
     long_description=open('README.txt').read(),
     # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
     classifiers=[
       "Programming Language :: Python",
       "Topic :: Software Development :: Libraries :: Python Modules",
       ],
     keywords='pyogp login awg virtualworlds',
     author='Pyogp collective',
     author_email='pyogp@lists.lindenlab.com',
     url='http://wiki.secondlife.com/wiki/Pyogp',
     license='Apache2',
     packages=find_packages(exclude=['ez_setup']),
     include_package_data=False,
     namespace_packages=['pyogp'],
     zip_safe=False,
     install_requires=[
         'setuptools',
         'pyogp.lib.client==0.1dev'
         ],
     entry_points={
         'console_scripts': [
             'AIS_inventory_handling = pyogp.apps.examples.AIS_inventory_handling:main',
             'agent_login = pyogp.apps.examples.agent_login:main',
             'agent_manager = pyogp.apps.examples.agent_manager:main',
             'appearance_management = pyogp.apps.examples.appearance_management:main',
             'chat_and_instant_messaging = pyogp.apps.examples.chat_and_instant_messaging:main',
             'client_proxy = pyogp.apps.proxy.client_proxy:main',
             'group_chat = pyogp.apps.examples.group_chat:main',
             'group_creation = pyogp.apps.examples.group_creation:main',
             'inventory_handling = pyogp.apps.examples.inventory_handling:main',
             'inventory_transfer = pyogp.apps.examples.inventory_transfer:main',
             'inventory_transfer_specify_agent = pyogp.apps.examples.inventory_transfer_specify_agent:main',
             'login = pyogp.apps.examples.login:main',
             'multi_agents_subprocess = pyogp.apps.examples.multi_agents_subprocess:main',
             'multi_region_connect = pyogp.apps.examples.multi_region_connect:main',
             'object_create_edit = pyogp.apps.examples.object_create_edit:main',
             'object_create_permissions = pyogp.apps.examples.object_create_permissions:main',
             'object_create_rez_script = pyogp.apps.examples.object_create_rez_script:main',
             'object_creation = pyogp.apps.examples.object_creation:main',
             'object_properties = pyogp.apps.examples.object_properties:main',
             'object_tracking = pyogp.apps.examples.object_tracking:main',
             'parcel_management = pyogp.apps.examples.parcel_management:main',
             'parse_packets = pyogp.apps.examples.parse_packets:main',
             'region_connect = pyogp.apps.examples.region_connect:main',
             'smoke_test = pyogp.apps.examples.smoke_test:main',
             
             ]
        }
     )

# extra entry points that aren't ready for use...
#            'webbot = pyogp.apps.web.django.pyogp_webbot.manage:main',
#            'proxy = pyogp.apps.examples.proxy:main',
#           'chat = pyogp.apps.examples.chat_interface:main',
