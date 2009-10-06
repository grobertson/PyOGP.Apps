
"""
Contributors can be viewed at:
http://svn.secondlife.com/svn/linden/projects/2008/pyogp/lib/base/trunk/CONTRIBUTORS.txt 

$LicenseInfo:firstyear=2008&license=apachev2$

Copyright 2009, Linden Research, Inc.

Licensed under the Apache License, Version 2.0.
You may obtain a copy of the License at:
    http://www.apache.org/licenses/LICENSE-2.0
or in 
    http://svn.secondlife.com/svn/linden/projects/2008/pyogp/lib/base/LICENSE.txt

$/LicenseInfo$
"""

from logging import getLogger

# standard modules
from webob import Request, Response
from wsgiref.simple_server import make_server
import xmlrpclib
import traceback
import optparse
import copy
import socket

# related
from indra.base import llsd
from eventlet import api

# pyogp.lib.base
from pyogp.lib.base.network.stdlib_client import StdLibClient, HTTPError
from pyogp.lib.base.message.circuit import Host
from pyogp.lib.base.network.net import NetUDPClient

# pyogp.lib.client
from pyogp.lib.client.login import Login

# initialize globals
logger = getLogger('pyogp.lib.client.login')
DEBUG = 1


class UDPProxy(object):
    """ proxies a Second Life viewer's UDP connection to a region """

    def __init__(self, sim_ip, sim_port, proxy_port):
        """ initialize a UDP proxy """

        self.target_sim_ip = sim_ip
        self.target_sim_port = sim_port

        # the outgoing connection to the grid
        self.udp_client = NetUDPClient()  # the sender, what we are proxying the target to 
        self.socket = self.udp_client.start_udp_connection()
        
        self.proxy_port = proxy_port      
        self.socket.bind((socket.gethostname(), proxy_port))

        self.start_udp_proxy()

        # the viewer's connection to localhost
        self.host = Host((self.target_sim_ip, self.target_sim_port))

        print 'Initializing a UDP proxy. Target IP: %s is proxied to %s' % (self.host, '127.0.0.1:%s' % (self.proxy_port))

    def start_udp_proxy(self):

        pass


class ViewerProxyApp(object):
    """ proxies a login request from a Second Life viewer """

    def __init__(self, loginuri, proxy_port_seed):

        self.loginuri = loginuri
        self.login_handler = Login()

        self.proxy_port_seed = proxy_port_seed
        self.ports = []

        print "Initialized the login proxy for %s" % self.loginuri

    def __call__(self, environ, start_response, ):

        self.environ = environ
        self.start = start_response

        self.request = Request(environ)

        self.response = Response()

        try:
            login_params = xmlrpclib.loads(self.request.body)

            response = self.login_handler._post_to_legacy_loginuri(self.loginuri, login_params = login_params[0][0], login_method = login_params[1], proxied = True)

            sim_ip = copy.copy(response['sim_ip'])  # swap out with localhost
            sim_port = copy.copy(response['sim_port'])  # swap out with a local port
            seed_cap = copy.copy(response['seed_capability'])   # swap out the seed cap with a localhost url

            proxy_port = self.proxy_port_seed + len(self.ports)

            udp_proxy = UDPProxy(sim_ip, sim_port, self.proxy_port_seed)

            # uncomment me to swap out the udp ip:port with local ones
            #response['sim_ip'] = '127.0.0.1'
            #response['sim_port'] = udp_proxy.proxy_port

            tuple_response = tuple([response])
            self.response.body = xmlrpclib.dumps(tuple_response)

            return self.response(environ, start_response)

        except Exception, e:

            print e

            return self.response(environ, start_response)

def main():

    print "i'm only proxying logins right now, stay tuned for more fun soon!"

    parser = optparse.OptionParser(
        usage='%prog --port=PORT'
        )
    parser.add_option(
        '--port',
        default='8080',
        dest='port',
        type='int',
        help='Port to serve on (default 8080)')
    parser.add_option(
        '--loginuri',
        default='https://login.aditi.lindenlab.com/cgi-bin/login.cgi',
        dest='loginuri',
        help='Specifies the target loginuri to connect proxy to')
    parser.add_option(
        '--proxy_port_seed',
        default=14000,
        dest='proxy_port_seed',
        type='int',
        help='Seed port to serve UDP on (default 14000)')

    options, args = parser.parse_args()

    # init the login proxy
    viewer_proxy = ViewerProxyApp(options.loginuri, options.proxy_port_seed)

    httpd = make_server('localhost', options.port, viewer_proxy)

    print 'Serving login requests on https://localhost:%s' % options.port

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print '^C'
    except:
        traceback.print_exc()

if __name__=="__main__":
    main()

