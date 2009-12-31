
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

# standard modules
import copy
import logging
import optparse
import socket
import traceback
from webob import Request, Response
from wsgiref.simple_server import make_server
import xmlrpclib

# related
from indra.base import llsd
from eventlet import api

# pyogp.lib.base
from pyogp.lib.base.network.stdlib_client import StdLibClient, HTTPError
from pyogp.lib.base.message.circuit import Host
from pyogp.lib.base.network.net import NetUDPClient
from pyogp.lib.base.message.udpdispatcher import UDPDispatcher

# pyogp.lib.client
from pyogp.lib.client.login import Login

# initialize globals
logger = logging.getLogger('pyogp.apps.examples.proxy')


class UDPProxy(object):
    """ proxies a Second Life viewer's UDP connection to a region """

    def __init__(self, sim_ip, sim_port):
        """ initialize a UDP proxy, mapping 2 ports to a single outbound port """
    
        self.target_host = Host((sim_ip, sim_port))
        self.local_host = None

        # the outgoing connection to the grid
        self.server_facing_udp_client = NetUDPClient()  # the sender, what we are proxying the target to 
        #self.server_facing_socket = self.server_facing_udp_client.start_udp_connection()
        self.server_facing_udp_dispatcher = UDPDispatcher(udp_client=self.server_facing_udp_client)

        # the local connection for the client
        self.viewer_facing_udp_client = NetUDPClient()  # the sender, what we are proxying the target to 
        #self.viewer_facing_socket = self.viewer_facing_udp_client.start_udp_connection()
        self.viewer_facing_udp_dispatcher = UDPDispatcher(udp_client=self.viewer_facing_udp_client)

        logger.debug("Building socket pair for %s udp proxy" % (self.target_host))

    def pin_udp_proxy_ports(self, viewer_facing_port, server_facing_port):

        try:

            # tell the sim_socket to be on a specific port
            logger.debug("Binding server_facing_socket to port %s" % (server_facing_port))
            self.server_facing_udp_dispatcher.socket.bind((socket.gethostname(), server_facing_port))

            # tell the local_socket to be on a specific port
            logger.debug("Binding viewer_facing_socket to port %s" % (viewer_facing_port))
            self.viewer_facing_udp_dispatcher.socket.bind((socket.gethostname(), viewer_facing_port))

            hostname = self.viewer_facing_udp_dispatcher.socket.getsockname()[0]

            self.local_host = Host((hostname, viewer_facing_port))
            
            return hostname

        except Exception, e:
            raise

    def start_proxy(self):

        logger.debug("Starting proxies in UDPProxy")

        self._is_running = True

        while self._is_running:

            try: 
                api.sleep(0)

                self._send_viewer_to_sim()
                self._receive_sim_to_viewer()
            except KeyboardInterrupt:
                logger.INFO("Stopping UDP proxy for %s" % (self.target_host))
                break
            except:
                traceback.print_exc()

    def _send_viewer_to_sim(self):

        logger.debug("Checking for msgs from viewer")

        msg_buf, msg_size = self.viewer_facing_udp_client.receive_packet(self.viewer_facing_udp_dispatcher.socket)
        recv_packet = self.viewer_facing_udp_dispatcher.receive_check(self.viewer_facing_udp_dispatcher.udp_client.get_sender(),
                                                        msg_buf, 
                                                        msg_size)
        
        #logger.debug("viewer_facing_udp_client.receive_packet got %s:%s" % (msg_buf, msg_size))

        if msg_size > 0:
            logger.debug("Sending from %s to %s! Data: len(%s) Host: %s" % (self.viewer_facing_udp_dispatcher.socket.getsockname(), self.server_facing_udp_dispatcher.socket.getsockname(), len(msg_buf), self.target_host))
            self.server_facing_udp_client.send_packet(self.server_facing_udp_dispatcher.socket, msg_buf, self.target_host)

    def _receive_sim_to_viewer(self):

        logger.debug("Checking for msgs from server")

        msg_buf, msg_size = self.server_facing_udp_client.receive_packet(self.server_facing_udp_dispatcher.socket)
        recv_packet = self.server_facing_udp_dispatcher.receive_check(self.server_facing_udp_dispatcher.udp_client.get_sender(),
                                                        msg_buf, 
                                                        msg_size)

        #logger.debug("server_facing_udp_client.receive_packet got %s:%s" % (msg_buf, msg_size))

        if msg_size > 0:
            logger.debug("Sending from %s to %s! Data: len(%s) Host: %s" % (self.server_facing_udp_dispatcher.socket.getsockname(), self.viewer_facing_udp_dispatcher.socket.getsockname(), len(msg_buf), self.target_host))
            self.viewer_facing_udp_client.send_packet(self.viewer_facing_udp_dispatcher.socket, msg_buf, self.local_host)

class ViewerProxyApp(object):
    """ proxies a login request from a Second Life viewer """

    def __init__(self, loginuri, port, proxy_port_seed, proxy_udp=True, proxy_caps=False):

        self.loginuri = loginuri
        self.login_port = port
        self.proxy_port_seed = proxy_port_seed
        
        self.proxy_udp = proxy_udp
        self.proxy_caps = proxy_caps

        self._is_running = True

        # initialize the login request
        #self.proxy_login()


    def start_udp_proxy(self, sim_ip, sim_port):

        logger.debug("ViewerProxyApp is spawning UDP proxies for %s:%s" % (sim_ip, sim_port))

        viewer_facing_port = self.proxy_port_seed
        server_facing_port = self.proxy_port_seed + 1
        self.proxy_port_seed += 2

        udp_proxy = UDPProxy(sim_ip, sim_port)
        hostname = udp_proxy.pin_udp_proxy_ports(viewer_facing_port, server_facing_port)
        
        api.spawn(udp_proxy.start_proxy)

        return hostname, viewer_facing_port

    def proxy_login(self):

        # init the login proxy
        login_proxy = LoginHandler(self)
        httpd = make_server('127.0.0.1', self.login_port, login_proxy)

        try:
            httpd.handle_request()
        except KeyboardInterrupt:
            print '^C'
        except:
            traceback.print_exc()

class LoginHandler(object):

    def __init__(self, caller):

        self.caller = caller
        self.loginuri = self.caller.loginuri
        self.port = self.caller.login_port

        self.login_handler = Login()

        logger.info("Proxying login requests for %s on https://127.0.0.1:%s" % (self.loginuri, self.port))

    def __call__(self, environ, start_response, ):

        self.environ = environ
        self.start = start_response

        self.request = Request(environ)

        self.response = Response()

        try:
            login_params = xmlrpclib.loads(self.request.body)

            response = self.login_handler._post_to_legacy_loginuri(self.loginuri, login_params = login_params[0][0], login_method = login_params[1], proxied = True)

            logger.debug("Login response is: %s" % (response))

            if response['login'] == 'true':
                sim_ip = copy.copy(response['sim_ip'])  # swap out with localhost
                sim_port = copy.copy(response['sim_port'])  # swap out with a local port
                seed_cap = copy.copy(response['seed_capability'])   # swap out the seed cap with a localhost url

                if self.caller.proxy_udp:
                    # get ports from the calling app to replace in the login response to the viewer
                    (local_ip, local_port) = self.caller.start_udp_proxy(sim_ip, sim_port)
                    
                    response['sim_ip'] = local_ip
                    response['sim_port'] = local_port
                
                if self.caller.proxy_caps:
                    response['seed_capability'] = "http://%s:%s" % (local_seed_cap_host.ip, local_seed_cap_host.port)
                    
            logger.debug("Transformed login response is: %s" % (response))

            tuple_response = tuple([response])
            self.response.body = xmlrpclib.dumps(tuple_response)

            return self.response(environ, start_response)

        except Exception, e:
            logger.error(e)
            traceback.print_exc()
            return self.response(environ, start_response)

def main():

    logger.debug("This script is only proxying logins right now.")

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

    # init logging
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG) # seems to be a no op, set it for the logger
    formatter = logging.Formatter('%(asctime)-30s%(name)-30s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.getLogger('').setLevel(logging.DEBUG)

    # init the viewer proxy
    viewer_proxy = ViewerProxyApp(options.loginuri, options.port, options.proxy_port_seed)

    api.spawn(viewer_proxy.proxy_login)

    while viewer_proxy._is_running:
        api.sleep(5)
        logger.debug("in main")

if __name__=="__main__":
    main()

