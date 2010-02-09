# Contributors can be viewed at:
# http://bitbucket.org/enus_linden/pyogp.apps/src/tip/CONTRIBUTORS.txt
#
# $LicenseInfo:firstyear=2008&license=apachev2$
#
# Copyright 2010, Linden Research, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# or in 
#     http://bitbucket.org/enus_linden/pyogp.apps/src/tip/LICENSE.txt
# 
# $/LicenseInfo$


# standard
import logging
from optparse import OptionParser
import os
import re
import subprocess
import sys
import time

# related
from eventlet import api

# pyogp
from pyogp.lib.client.agentmanager import AgentManager
from pyogp.lib.client.agent import Agent
from pyogp.lib.client.settings import Settings

logger = logging.getLogger("OI_tester")

# this is a one off script, and as such is simple
# easy enough to refactor should the need arise later 

def login():
    """ login an to a login endpoint """ 

    parser = OptionParser(usage="usage: %prog --file filename [options]")

    parser.add_option("-f", "--farm",
                        dest="farm",
                        default="aditi",
                        help="farm to create test accounts on")
    parser.add_option("-l", "--loginuri", 
                        dest="loginuri", 
                        default="https://login.aditi.lindenlab.com/cgi-bin/login.cgi",
                        help="specified the target loginuri")
    parser.add_option("-c", "--count", 
                        dest="count", 
                        default=0, 
                        help="number of agents to login")
    parser.add_option("-s", "--scriptsdir",
                        dest="scriptsdir",
                        default="/local/linden/scripts",
                        help="location of the scripts dir (checkout/install)")
    parser.add_option("-d", "--delay",
                        dest="delay",
                        default=0,
                        help="delay between logins (defaults to 0)")
    scriptname = "create_user.pl"

    (options, args) = parser.parse_args()

    # initialize logging
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG) # seems to be a no op, set it for the logger
    formatter = logging.Formatter('%(asctime)-30s%(name)-30s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.getLogger('').setLevel(logging.INFO)

    # do some param validation
    if int(options.count) == 0:
        print "Must specify some number > 0 of accounts to create and login"
        sys.exit()

    if not os.path.isdir(options.scriptsdir):
        print "%s does not exist, where is your checkout or install?" % (options.scriptsdir)
        sys.exit()

    script = os.path.join(options.scriptsdir, scriptname)

    if not os.path.isfile(script):
        print "%s does not exist, where is your checkout or install?" % (script)
        sys.exit()

    delay = int(options.delay)

    # prep instance settings, disable some unnecessary things
    settings = Settings()
    settings.ENABLE_OBJECT_TRACKING = False
    settings.MULTIPLE_SIM_CONNECTIONS = False
    settings.ENABLE_REGION_EVENT_QUEUE = False
    settings.ENABLE_PARCEL_TRACKING = False
    settings.ENABLE_INVENTORY_MANAGEMENT = False


    clients = []
    agents = []

    # create agents on the grid via the standard scripts/create_user.pl script
    # Enus has a lib-style create_user.py in the works, almost done.
    # firstname = timestamp
    # lastname = (default LLQAbot, id - 5644)
    # password = firstname mod
    # email = firstname@lindenlab.com
    # ./create_user.pl --farm aditi --firstname create_user 
    #           --lastname 5644 --password lindentest --email enus@lindenlab.com

    firstname_seed = 'OITest'
    lastname_id = 5644
    lastname = 'LLQABot'

    logger.info("Creating %s accounts for use in test pass." % (options.count))

    for i in range(int(options.count)):
        timestamp = str(int(time.time()))
        timestamp = timestamp[len(timestamp)-6:]
        firstname = "%s%s%s" % (firstname_seed, i, timestamp)
        password = firstname
        email = "%s%s" % (firstname, '@lindenlab.com')

        #logger.info("Creating %s %s with password of %s" % 
        #            (firstname, lastname, password))

        #cmd = "%s --farm %s --firstname %s --lastname %s --password %s --email %s" %
        #    (script, options.farm, firstname, lastname, password, email)

        cmd = [script, '--farm', options.farm, '--firstname', firstname, 
                '--lastname', str(lastname_id), '--password', password, '--email', email]

        #logger.info("Running %s" % (cmd))

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # test for success
        # HACKy
        result = p.stdout.read()

        if re.match("Sucessfully", result):
            logger.info("Successfully created %s %s" % (firstname, lastname))
            clients.append([firstname, lastname, password])
        else:
            logger.error("Failed to create %s %s" %(firstname, lastname))
            logger.error("Terminal failure state. Stopping.")
            sys.exit()

    # Now let's prime the accounts for login
    for params in clients:
        #First, initialize the agent
        agents.append(Agent(settings, params[0], params[1], params[2]))

    agentmanager = AgentManager()
    agentmanager.initialize(agents)

    try:
        # log them in
        for key in agentmanager.agents:
            api.sleep(delay)
            agentmanager.login(key, options.loginuri)

        while agentmanager.has_agents_running():
            api.sleep(0)
    # work around greenlet complaining about getting killed
    except AssertionError, e:
        pass


    # wrap up and dump stuff to stdout
    for fella in agentmanager.agents:
        print "Agent %s was in %s" % (agentmanager.agents[fella].Name(), agentmanager.agents[fella].region.SimName)


def main():
    return login()    

if __name__=="__main__":
    main()


