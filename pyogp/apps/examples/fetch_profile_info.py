# standard
import re
import getpass, sys, logging
from optparse import OptionParser

# related
from eventlet import api

# pyogp
from pyogp.lib.client.agent import Agent
from pyogp.lib.client.settings import Settings
from pyogp.lib.client.enums import AssetType
from pyogp.lib.base.datatypes import UUID

# pyogp messaging
from pyogp.lib.base.message.message import Message, Block


def login():
    """ login an to a login endpoint """ 

    parser = OptionParser(usage="usage: %prog [options] firstname lastname target_agent_id")

    logger = logging.getLogger("client.example")

    parser.add_option("-l", "--loginuri", dest="loginuri", default="https://login.aditi.lindenlab.com/cgi-bin/login.cgi",
                      help="specified the target loginuri")
    parser.add_option("-r", "--region", dest="region", default=None,
                      help="specifies the region (regionname/x/y/z) to connect to")
    parser.add_option("-q", "--quiet", dest="quiet", default=False, action="store_true",
                    help="log warnings and above (default is debug)")
    parser.add_option("-d", "--verbose", dest="verbose", default=False, action="store_true",
                    help="log info and above (default is debug)")
    parser.add_option("-p", "--password", dest="password", default=None,
                      help="specifies password instead of being prompted for one")

    (options, args) = parser.parse_args()

    if len(args) != 3:
        parser.error("Expected 3 arguments")

    (firstname, lastname, target_agent_id) = args
    
                
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)-30s%(name)-30s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

        # setting the level for the handler above seems to be a no-op
        # it needs to be set for the logger, here the root logger
        # otherwise it is NOTSET(=0) which means to log nothing.
    if options.verbose:
        logging.getLogger('').setLevel(logging.INFO)
    elif options.quiet:
        logging.getLogger('').setLevel(logging.WARNING)
    else:
        logging.getLogger('').setLevel(logging.DEBUG)

    # example from a pure agent perspective

    #grab a password!
    if options.password:
        password = options.password
    else:
        password = getpass.getpass()

    # prep instance settings
    settings = Settings()

    settings.ENABLE_INVENTORY_MANAGEMENT = False
    settings.ENABLE_COMMUNICATIONS_TRACKING = False
    settings.ENABLE_OBJECT_TRACKING = False
    settings.ENABLE_UDP_LOGGING =True
    settings.ENABLE_EQ_LOGGING = True
    settings.ENABLE_CAPS_LOGGING = True
    settings.MULTIPLE_SIM_CONNECTIONS = False

    #First, initialize the agent
    client = Agent(settings)

    # Now let's log it in
    api.spawn(client.login, options.loginuri, firstname, lastname, password, start_location = options.region, connect_region = True)

    # wait for the agent to connect to it's region
    while client.connected == False:
        api.sleep(0)

    while client.region.connected == False:
        api.sleep(0)

    fetch_agent_properties(client, target_agent_id, callback=lambda x: client.logout())

    while client.running:
        api.sleep(0)


def fetch_agent_properties(client, agent_id, callback=None):

    # Send AvatarPropertiesRequest
    # Get back AvatarPropertiesReply

    def onAgentPropertiesReply(packet):
        if repr(packet['AgentData'][0]['AvatarID']) == agent_id:

            block = packet['PropertiesData'][0]
            for prop in ['ImageID', 'FLImageID', 'PartnerID',
                         'AboutText', 'FLAboutText', 'BornOn',
                         'ProfileURL', 'CharterMember', 'Flags']:
                print "%s: %s" % (prop, block[prop])

            if callback:
                callback(packet)

    client.region.message_handler.register('AvatarPropertiesReply').subscribe(onAgentPropertiesReply)

    packet = Message('AvatarPropertiesRequest',
                     Block('AgentData',
                           AgentID = client.agent_id,
                           SessionID = client.session_id,
                           AvatarID = UUID(agent_id)))

    client.region.enqueue_message(packet)
    
    



def main():
    return login()    

if __name__=="__main__":
    main()

"""
Contributors can be viewed at:
http://svn.secondlife.com/svn/linden/projects/2008/pyogp/CONTRIBUTORS.txt 

$LicenseInfo:firstyear=2008&license=apachev2$

Copyright 2009, Linden Research, Inc.

Licensed under the Apache License, Version 2.0 (the "License").
You may obtain a copy of the License at:
    http://www.apache.org/licenses/LICENSE-2.0
or in 
    http://svn.secondlife.com/svn/linden/projects/2008/pyogp/LICENSE.txt

$/LicenseInfo$
"""

