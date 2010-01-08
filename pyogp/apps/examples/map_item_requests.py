# standard
import re
import getpass, sys, logging
from optparse import OptionParser

# related
from eventlet import api

# pyogp
from pyogp.lib.client.agent import Agent
from pyogp.lib.client.region import Region
from pyogp.lib.client.settings import Settings
from pyogp.lib.client.enums import AssetType
from pyogp.lib.base.datatypes import UUID

# pyogp messaging
from pyogp.lib.base.message.message import Message, Block


log = logging.getLogger('map_item_request')

def login():
    """ login an to a login endpoint """ 

    parser = OptionParser(usage="usage: %prog [options] firstname lastname groupname")

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

    parser.add_option("-m", "--message", dest="message", default=None,
                      help="The message to chat")

    (options, args) = parser.parse_args()

    if len(args) != 3:
        parser.error("Expected 3 arguments")

    (firstname, lastname, region_name) = args
    
                
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

    AgentLocationFinder(client, region_name)

    while client.running:
        api.sleep(0)



def region_name_to_handle_x_y(client, region_name, callback):
    handler = client.region.message_handler.register('MapBlockReply')

    def onMapBlockReplyPacket(packet):
        """ handles the MapBlockReply message from a simulator """

        for data in packet['Data']:

            if data['Name'].lower() == region_name.lower():

                # Stop listening once we have the data we asked for
                handler.unsubscribe(onMapBlockReplyPacket)

                region_handle = Region.xy_to_handle(data['X'], data['Y'])

                callback(region_handle, data['X'], data['Y'])
                return

        # Keep listening, as the event may come later

    # Register a handler for the response        
    handler.subscribe(onMapBlockReplyPacket)

    packet = Message('MapNameRequest', 
                    Block('AgentData', 
                        AgentID = client.agent_id, 
                        SessionID = client.session_id,
                        Flags = 0,
                        EstateID = 0, # filled in on server
                        Godlike = False), # filled in on server
                    Block('NameData',
                        Name = region_name.lower()))

    client.region.enqueue_message(packet) 


MAP_ITEM_TELEHUB = 0x01;
MAP_ITEM_PG_EVENT = 0x02;
MAP_ITEM_MATURE_EVENT = 0x03;
#MAP_ITEM_POPULAR = 0x04;
#MAP_ITEM_AGENT_COUNT = 0x05;
MAP_ITEM_AGENT_LOCATIONS = 0x06;
MAP_ITEM_LAND_FOR_SALE = 0x07;
MAP_ITEM_CLASSIFIED = 0x08;
MAP_ITEM_ADULT_EVENT = 0x09;
MAP_ITEM_LAND_FOR_SALE_ADULT = 0x0a;


REGION_WIDTH = 256

class AgentLocationFinder:

    def __init__(self, client, region_name):
        self.client = client
        self.region_name = region_name
        self.region_handle = None
        self.region_x = None
        self.region_y = None

        handler = self.client.region.message_handler.register('MapItemReply')
        handler.subscribe(self.onMapItemReply)

        region_name_to_handle_x_y(self.client, region_name, self.onRegionHandle)

    def onRegionHandle(self, region_handle, x, y):
        self.region_handle = region_handle
        self.region_x = x
        self.region_y = y

        if region_handle:

            packet = Message('MapItemRequest', 
                             Block('AgentData', 
                                   AgentID = self.client.agent_id, 
                                   SessionID = self.client.session_id,
                                   Flags = 0,
                                   EstateID = 0, # filled in on server
                                   Godlike = False), # filled in on server
                             Block('RequestData',
                                   ItemType = MAP_ITEM_AGENT_LOCATIONS,
                                   RegionHandle = region_handle))

            self.client.region.enqueue_message(packet)

        else:
            print "Unable to find region handle for:", self.region_name


    def onMapItemReply(self, packet):
        #print "Got map item reply:", packet
        item_type = packet['RequestData'][0]['ItemType']
        if item_type == MAP_ITEM_AGENT_LOCATIONS:
            for data in packet['Data']:
                x = data['X']
                y = data['Y']
                count = data['Extra']

                if int(x/REGION_WIDTH) == self.region_x and int(y/REGION_WIDTH) == self.region_y:

                    if count:
                        print "%d agent(s) at %d, %d" % (count, x % REGION_WIDTH, y % REGION_WIDTH)
                    else:
                        print "No agents present"
                    

def main():
    return login()    

if __name__=="__main__":
    main()

"""
Contributors can be viewed at:
http://svn.secondlife.com/svn/linden/projects/2008/pyogp/CONTRIBUTORS.txt 

$LicenseInfo:firstyear=2010&license=apachev2$

Copyright 2010, Linden Research, Inc.

Licensed under the Apache License, Version 2.0 (the "License").
You may obtain a copy of the License at:
    http://www.apache.org/licenses/LICENSE-2.0
or in 
    http://svn.secondlife.com/svn/linden/projects/2008/pyogp/LICENSE.txt

$/LicenseInfo$
"""

