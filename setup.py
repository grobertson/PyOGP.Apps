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
     dependency_links=['https://svn.secondlife.com/svn/linden/projects/2008/pyogp/pyogp.lib.base/tags/0.1/dist/'],
     version=version,
     description="basic pyogp apps package",
     long_description="skipping",
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
     zip_safe=False,
     install_requires=[
         'setuptools',
         'pyogp.lib.base'
         ],
     entry_points={
         'console_scripts': [
             'AIS_inventory_handling = pyogp.lib.base.examples.AIS_inventory_handling:main',
             'agent_login = pyogp.lib.base.examples.agent_login:main',
             'agent_manager = pyogp.lib.base.examples.agent_manager:main',
             'appearance_management = pyogp.lib.base.examples.appearance_management:main',
             'chat_and_instant_messaging = pyogp.lib.base.examples.chat_and_instant_messaging:main',
             'group_chat = pyogp.lib.base.examples.group_chat:main',
             'group_creation = pyogp.lib.base.examples.group_creation:main',
             'inventory_handling = pyogp.lib.base.examples.inventory_handling:main',
             'inventory_transfer = pyogp.lib.base.examples.inventory_transfer:main',
             'inventory_transfer_specify_agent = pyogp.lib.base.examples.inventory_transfer_specify_agent:main',
             'login = pyogp.lib.base.examples.login:main',
             'multi_region_connect = pyogp.lib.base.examples.multi_region_connect:main',
             'object_create_edit = pyogp.lib.base.examples.object_create_edit:main',
             'object_create_permissions = pyogp.lib.base.examples.object_create_permissions:main',
             'object_create_rez_script = pyogp.lib.base.examples.object_create_rez_script:main',
             'object_creation = pyogp.lib.base.examples.object_creation:main',
             'object_properties = pyogp.lib.base.examples.object_properties:main',
             'object_tracking = pyogp.lib.base.examples.object_tracking:main',
             'parcel_management = pyogp.lib.base.examples.parcel_management:main',
             'region_connect = pyogp.lib.base.examples.region_connect:main',
             'smoke_test = pyogp.lib.base.examples.smoke_test:main',
             ]
        }
     )
