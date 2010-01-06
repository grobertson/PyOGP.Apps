
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
import random
import signal
import sys
import traceback
from webob import Request, Response
from wsgiref.simple_server import make_server
import xmlrpclib

# related
from indra.base import llsd
from eventlet import api

# pyogp.lib.base
from pyogp.lib.base.caps_proxy import CapabilitiesProxy
from pyogp.lib.base.message.udpproxy import UDPProxy

# pyogp.lib.client
from pyogp.lib.client.login import Login

# initialize globals
logger = logging.getLogger('pyogp.apps.examples.proxy')

class ViewerProxyApp(object):
    """ proxies a login request from a Second Life viewer """

    def __init__(self, loginuri, login_port, proxy_udp=True, proxy_caps=True):

        self.loginuri = loginuri
        self.login_port = login_port
        
        self.proxy_udp = proxy_udp
        self.proxy_caps = proxy_caps

        self._is_running = True

        # let the login req proxy handle the first signal
        self.signal_handler = None

    def start_udp_proxy(self, sim_ip, sim_port):

        # signal handler to capture erm signals
        if not self.signal_handler:
            self.signal_handler = signal.signal(signal.SIGINT, self.sigint_handler)

        logger.debug("ViewerProxyApp is spawning UDP proxies for %s:%s" % (sim_ip, sim_port))

        viewer_facing_port = random.randrange(14001, 15000)
        server_facing_port = random.randrange(15001, 16000)

        self.udp_proxy = UDPProxy(sim_ip, sim_port, viewer_facing_port, server_facing_port)
        
        api.spawn(self.udp_proxy.start_proxy)

        return self.udp_proxy.hostname, self.udp_proxy.proxy_socket.getsockname()[1]

    def start_caps_proxy(self, seed_cap_url, caps_proxy_port=None):

        # signal handler to capture erm signals
        if not self.signal_handler:
            self.signal_handler = signal.signal(signal.SIGINT, self.sigint_handler)
        
        logger.debug("ViewerProxyApp is spawning caps proxies for region with\
                        seed_capability of %s" % (seed_cap_url))

        if not caps_proxy_port:
            caps_proxy_port = random.randrange(16001, 17001)

        self.caps_proxy = CapabilitiesProxy(seed_cap_url, '127.0.0.1', caps_proxy_port)

        api.spawn(self.start_caps_proxy_service, '127.0.0.1', caps_proxy_port, self.caps_proxy)

        return '127.0.0.1', caps_proxy_port, self.caps_proxy.proxy_map[seed_cap_url]

    def start_caps_proxy_service(self, caps_proxy_ip, caps_proxy_port, app):

        httpd = make_server(caps_proxy_ip, caps_proxy_port, self.caps_proxy)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            sys.exit()
        except:
            traceback.print_exc()
        '''
        
        while self._is_running:
            api.sleep(0)
            try:
                httpd.handle_request()
            except KeyboardInterrupt:
                sys.exit()
            except:
                traceback.print_exc()
        '''


    def proxy_login(self):

        # init the login proxy
        login_proxy = LoginHandler(self)
        httpd = make_server('127.0.0.1', self.login_port, login_proxy)

        try:
            httpd.handle_request()
        except KeyboardInterrupt:
            sys.exit()
        except:
            traceback.print_exc()

    def sigint_handler(self, signal_sent, frame):
        """ catches terminal signals (Ctrl-C) to kill running client instances """

        logger.warning("Caught signal... %d. Stopping" % signal_sent)
        
        if hasattr(self, 'udp_proxy'):
            self.udp_proxy._is_running = False
        self._is_running = False

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

            #logger.debug("Login response is: %s" % (response))

            if response['login'] == 'true':
                sim_ip = copy.copy(response['sim_ip'])  # swap out with localhost
                sim_port = copy.copy(response['sim_port'])  # swap out with a local port
                seed_cap = copy.copy(response['seed_capability'])   # swap out the seed cap with a localhost url

                if self.caller.proxy_udp:
                    # get ports from the calling app to replace in the login response to the viewer
                    (local_ip, local_port) = self.caller.start_udp_proxy(sim_ip, sim_port)
                    
                    response['sim_ip'] = local_ip
                    response['sim_port'] = local_port
                    
                    #logger.debug("Replacing login response sim_ip:sim_port %s:%s with proxy of %s:%s" %  (sim_ip, sim_port, response['sim_ip'], response['sim_port']))
                
                if self.caller.proxy_caps:
                    (local_ip, local_port, path) = self.caller.start_caps_proxy(seed_cap)
                    response['seed_capability'] = "http://%s:%s/%s" % (local_ip, local_port, path)
                    
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
        dest='login_port',
        type='int',
        help='Port to serve on (default 8080)')
    parser.add_option(
        '--loginuri',
        default='https://login.aditi.lindenlab.com/cgi-bin/login.cgi',
        dest='loginuri',
        help='Specifies the target loginuri to connect proxy to')
    parser.add_option(
        '-v', '--verbose',
        default=False,
        dest='verbose',
        action="store_true",
        help='enables logging, sets logging level to info, logs names of all \
            packets')
    parser.add_option(
        '-V', '--verboseverbose',
        default=False,
        dest='verboseverbose',
        action="store_true",
        help='enables logging, sets logging level to debug, logs contents \
            of all packets')

    options, args = parser.parse_args()

    # init logging
    if options.verbose or options.verboseverbose:
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG) # seems to be a no op, set it for the logger
        formatter = logging.Formatter('%(asctime)-30s%(name)-30s: %(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
        if options.verbose:
            logging.getLogger('').setLevel(logging.INFO)
        elif options.verboseverbose:
            logging.getLogger('').setLevel(logging.DEBUG)
        else:
            logging.getLogger('').setLevel(logging.WARNING)

    # init the viewer proxy
    viewer_proxy = ViewerProxyApp(options.loginuri, options.login_port)

    api.spawn(viewer_proxy.proxy_login)

    while viewer_proxy._is_running:
        api.sleep(5)

if __name__=="__main__":
    main()

