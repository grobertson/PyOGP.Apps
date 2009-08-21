# standard
import re
import getpass, sys, logging
from optparse import OptionParser

# setup
import setup_path

# pyogp
from pyogp.lib.base.agent import Agent
from pyogp.lib.base.utilities.enums import DeRezDestination, AssetType, \
     InventoryType, WearablesIndex
from pyogp.lib.base.datatypes import UUID, Vector3

# related
from eventlet import api


class Semaphore(object):
    """
    Basic semaphore to allow the serialization of the tests
    """
    waiting = True

    def wait(self):
        while self.waiting:
            api.sleep(0)
        self.waiting = True

    def signal(self):
        self.waiting = False

def login():
    """ login an to a login endpoint """ 

    parser = OptionParser(usage="usage: %prog [options] firstname lastname")

    logger = logging.getLogger("pyogp.lib.base.example")

    parser.add_option("-l", "--loginuri", dest="loginuri", default="https://login.aditi.lindenlab.com/cgi-bin/login.cgi",
                      help="specified the target loginuri")
    parser.add_option("-r", "--region", dest="region", default=None,
                      help="specifies the region (regionname/x/y/z) to connect to")
    parser.add_option("-q", "--quiet", dest="verbose", default=True, action="store_false",
                    help="enable verbose mode")


    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.error("Expected arguments: firstname lastname")

    if options.verbose:
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG) # seems to be a no op, set it for the logger
        formatter = logging.Formatter('%(asctime)-30s%(name)-30s: %(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

        # setting the level for the handler above seems to be a no-op
        # it needs to be set for the logger, here the root logger
        # otherwise it is NOTSET(=0) which means to log nothing.
        logging.getLogger('').setLevel(logging.DEBUG)
    else:
        print "Attention: This script will print nothing if you use -q. So it might be boring to use it like that ;-)"

    # example from a pure agent perspective

    #grab a password!
    password = getpass.getpass()

    #First, initialize the agent
    client = Agent()

    # Now let's log it in
    client.login(options.loginuri, args[0], args[1], password, start_location = options.region)

    # wait for the agent to connect
    while client.connected == False:
        api.sleep(0)

    # let things settle down
    while client.Position == None:
        api.sleep(0)

    # for folders whose parent = root folder aka My Inventory, request their contents
    [client.inventory._request_folder_contents(folder.FolderID) for folder in client.inventory.folders if folder.ParentID == client.inventory.inventory_root.FolderID]
    
    
    api.sleep(5)
    
    for attr in client.__dict__:
        print attr, ':\t\t\t',  client.__dict__[attr]

    return client

def test_login(client):
    pass

def test_walk(client):
    client.walk()
    api.sleep(5)
    client.walk(False)
    api.sleep(5)

def test_fly(client):
    client.fly()
    api.sleep(5)
    client.fly(False)
    api.sleep(5)
    
def test_im(client):
    """
    Tests im by sending an im to self and verify it is received
    """
    s = Semaphore()
    im_handler = client.events_handler.register('InstantMessageReceived')
    def im_received(message_info):
        if str(message_info.payload['FromAgentID']) == \
           str(client.agent_id):
            
            s.signal()
    im_handler.subscribe(im_received)
    client.instant_message(client.agent_id, "Smoke Test message")
    s.wait()
    #verify message_info
    
def test_chat(client):
    """
    Tests chat sending a global chat and verify that it is received.
    """
    s = Semaphore()
    chat_handler = client.events_handler.register('ChatReceived')
    def chat_received(message_info):
        s.signal()
    chat_handler.subscribe(chat_received)
    client.say("Smoke Test chat")
    s.wait()
    #verify message_info

def test_create_object(client):
    """
    Tests object creation by rezzing a new prim, selecting it, and
    then derezzing it.
    """
    s = Semaphore()
    object_handler = client.events_handler.register('ObjectSelected')
    def object_created(object_info):
        prim = object_info.payload['object']
        matches = client.inventory.search_inventory(client.inventory.folders,
                                                    name="Objects")
        folder = matches.pop()
        transaction_id = UUID()
        transaction_id.random()
        prim.derez(client,
                   DeRezDestination.TakeIntoAgentInventory,
                   folder.FolderID,
                   transaction_id,
                   client.active_group_id)
        s.signal()
    
    object_handler.subscribe(object_created)
    client.region.objects.create_default_box()
    s.wait()
    #verify object copied to inventory

def test_create_and_remove_item_in_inventory(client):
    """
    Tests item can be created and removed from the inventory
    """
    s = Semaphore()
    matches = client.inventory.search_inventory(client.inventory.folders,
                                                name='Notecards')
    folder = matches.pop()
    def inventory_item_created(item):
        s.signal()
    item_name = "Smoke Test notecard"
    item_desc = "Smoke Test desc"
    client.inventory.create_new_item(folder,
                                     item_name,
                                     item_desc, 
                                     AssetType.Notecard,
                                     InventoryType.Notecard,
                                     WearablesIndex.WT_SHAPE,
                                     0,
                                     inventory_item_created)
    s.wait()
    #verify item created in inventory                                     
    matches = client.inventory.search_inventory(client.inventory.folders,
                                                name=item_name)
    item = matches.pop()
    api.sleep(5)
    client.inventory.send_RemoveInventoryItem(client.agent_id,
                                              client.session_id,
                                              item.ItemID)
    #verify item removed
    api.sleep(5)
    
def test_wear_something(client):
    #check current pants
    matches = client.inventory.search_inventory(client.inventory.folders,
                                      name="Clubgoer Male Pants")
    item = matches.pop()
    client.appearance.wear_item(item, WearablesIndex.WT_PANTS)
    api.sleep(10)
    #verify avatar is wearing item
    #switch pants back
    #verify old pants
    
def test_can_teleport(client):
    # teleport to a new position
    client.teleport(region_handle=client.region.RegionHandle,
                    position=Vector3(X=180, Y=180, Z=30))
    # verify position
    # teleport back
    # verify position

def test_physics(client):
    pass

def main():

    client = login()    
    test_im(client)
    test_chat(client)
    test_create_object(client)
    test_create_and_remove_item_in_inventory(client)
    #test_fly(client)
    test_walk(client)
    test_can_teleport(client)
    test_wear_something(client)
    client.logout()
    
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

