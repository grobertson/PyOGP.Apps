
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

# standard
import unittest
import getpass, logging
from optparse import OptionParser
import time

# pyogp
from pyogp.lib.client.agent import Agent
from pyogp.lib.client.enums import DeRezDestination, AssetType, \
     InventoryType, WearablesIndex
from pyogp.lib.base.datatypes import UUID, Vector3

# related
from eventlet import api

client = Agent()

class Semaphore(object):
    """
    Basic semaphore to allow the serialization of the tests
    """
    waiting = True
    timed_out = False
    
    def wait(self, time_out=0):
        start = now = time.time()
        while self.waiting and now - start <= time_out:
            api.sleep(0)
            now = time.time()
        if now - start > time_out:
            self.timed_out = True
        self.waiting = True
        
    def signal(self):
        self.waiting = False

def login():
    """ login an to a login endpoint """ 

    parser = OptionParser(usage="usage: %prog [options] firstname lastname")

    logger = logging.getLogger("client.example")

    parser.add_option("-l", "--loginuri", dest="loginuri",
                      default="https://login.aditi.lindenlab.com/cgi-bin/login.cgi",
                      help="specified the target loginuri")
    parser.add_option("-r", "--region", dest="region", default=None,
                      help="specifies the region (regionname/x/y/z) to connect to")
    parser.add_option("-q", "--quiet", dest="verbose", default=True,
                      action="store_false", help="enable verbose mode")
    parser.add_option("-p", "--password", dest="password", default=None,
                      help="specifies password instead of being prompted for one")
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
    if options.password:
        password = options.password
    else:
        password = getpass.getpass()

    # Now let's log it in
    client.login(options.loginuri, args[0], args[1], password,
                 start_location=options.region)

    # wait for the agent to connect
    while client.connected == False:
        api.sleep(0)

    # let things settle down
    while client.Position == None:
        api.sleep(0)

    # for folders whose parent = root folder aka My Inventory, request their contents
    [client.inventory._request_folder_contents(folder.FolderID) \
     for folder in client.inventory.folders if folder.ParentID == \
     client.inventory.inventory_root.FolderID]
    
    api.sleep(10)
    
    for attr in client.__dict__:
        print attr, ':\t\t\t',  client.__dict__[attr]

    return client

class TestServer(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        api.sleep(3)
    
                
    def test_im(self):
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
        s.wait(30)
        self.assertFalse(s.timed_out)
    
    def test_chat(self):
        """
        Tests chat sending a global chat and verify that it is received.
        """
        s = Semaphore()
        chat_handler = client.events_handler.register('ChatReceived')
        msg = "Smoke Test chat"
        def chat_received(message_info):
            if message_info.payload['Message'] == msg:
                s.signal()
        chat_handler.subscribe(chat_received)
        client.say(msg)
        s.wait(30)
        self.assertFalse(s.timed_out)
    
    def test_create_object(self):
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
        s.wait(30)
        self.assertFalse(s.timed_out)
        #verify object copied to inventory

    def test_create_and_remove_item_in_inventory(self):
        """
        Tests item can be created and removed from the inventory
        """
        s = Semaphore()
        matches = client.inventory.search_inventory(client.inventory.folders,
                                                    name='Notecards')
        folder = matches.pop()
        def inventory_item_created(item):
            s.signal()
        item_name = "Smoke Test notecard" + str(time.time())
        item_desc = "Smoke Test desc"
        client.inventory.create_new_item(folder,
                                         item_name,
                                         item_desc, 
                                         AssetType.Notecard,
                                         InventoryType.Notecard,
                                         WearablesIndex.WT_SHAPE,
                                         0,
                                         inventory_item_created)
        s.wait(30)
        self.assertFalse(s.timed_out)

        #verify item created in inventory                                     
        matches = client.inventory.search_inventory(client.inventory.folders,
                                                    name=item_name)
        self.assertTrue(len(matches) > 0)
        item = matches.pop()
        api.sleep(5)
        client.inventory.remove_inventory_item(item,
                                               folder,
                                               client.inventory.folders)
        #verify item removed
        client.inventory.sendFetchInventoryDescendentsRequest(folder.FolderID)
        api.sleep(5)        
        matches = client.inventory.search_inventory(client.inventory.folders,
                                                    name=item_name)
        self.assertTrue(len(matches) == 0)
        
    '''
    def test_wear_something(self):
        """
        Tests wearing something by finding a clothing item in the inventory,
        wearing it and verifying it is worn.
        """
        #check current pants
        matches = client.inventory.search_inventory(client.inventory.folders,
                                                    name="Clubgoer Male Pants")
        item = matches.pop()
        client.appearance.wear_item(item, WearablesIndex.WT_PANTS)
        api.sleep(10)
        #verify avatar is wearing item
        #switch pants back
        #verify old pants

    '''
    def test_can_walk(self):
        """
        Tests walking by walking for 5 seconds and verifying position change
        """
        old_pos = Vector3(X=client.Position.X,
                          Y=client.Position.Y,
                          Z=client.Position.Z)
        client.walk()
        api.sleep(5)
        client.walk(False)
        api.sleep(5)
        self.assertFalse(client.Position.X == old_pos.X and \
                         client.Position.Y == old_pos.Y and \
                         client.Position.Z == old_pos.Z)

    def test_can_teleport(self):
        """
        Tests teleport by teleporting to a new location and verifying position
        has changed
        """
        old_pos = Vector3(X=client.Position.X,
                          Y=client.Position.Y,
                          Z=client.Position.Z)
        new_pos = Vector3(X=client.Position.X + 5,
                          Y=client.Position.Y + 5,
                          Z=client.Position.Z)
        client.teleport(region_handle=client.region.RegionHandle,
                        position=new_pos)
        api.sleep(5)  # wait for object update
        self.assertFalse(client.Position.X == old_pos.X and \
                         client.Position.Y == old_pos.Y and \
                         client.Position.Z == old_pos.Z)

        client.teleport(region_handle=client.region.RegionHandle,
                        position=old_pos)

    def test_physics(self):
        """
        Physics by flying up, stopping, and verify avatar's position changes
        every second over 5 seconds.
        """
        client.fly()
        client.up()
        api.sleep(3)
        old_pos = Vector3(X=client.Position.X,
                          Y=client.Position.Y,
                          Z=client.Position.Z)
        client.up(False)
        client.fly(False)
        api.sleep(5)
        new_pos = Vector3(X=client.Position.X,
                          Y=client.Position.Y,
                          Z=client.Position.Z)
        self.assertFalse(new_pos.X == old_pos.X and \
                         new_pos.Y == old_pos.Y and \
                         new_pos.Z == old_pos.Z)

    def test_fly(self):
        """
        Tests flying by flying for 5 seconds and verifying position change
        """
        old_pos = Vector3(X=client.Position.X,
                          Y=client.Position.Y,
                          Z=client.Position.Z)
        client.fly()
        api.sleep(5)
        self.assertFalse(client.Position.X == old_pos.X and \
                         client.Position.Y == old_pos.Y and \
                         client.Position.Z == old_pos.Z)
        client.fly(False)

def main():    
    client = login()    
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestServer))
    unittest.TextTestRunner().run(suite)
    client.logout()

if __name__ == "__main__":
    main()
