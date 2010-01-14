
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

# standard
import base64
from logging import getLogger
from webob import Request, Response
from wsgiref.simple_server import make_server

# related
from llbase import llsd
from eventlet import util

# the following makes socket calls nonblocking. magic
util.wrap_socket_with_coroutine_socket()

# pyogp
from pyogp.lib.base.datatypes import UUID
from pyogp.lib.base.event_queue import EventQueueClient
from pyogp.lib.base.exc import DataParsingError, HTTPError

# initialize logging
logger = getLogger('client_proxy.lib.caps_proxy')

class CapabilitiesProxy(object):
    """ an application class for wsgiref.simple_server which handles
    proxyied http requests and responses for capabilities """

    def __init__(self,
                seed_cap_url,
                proxy_host_ip,
                proxy_host_port,
                caller,
                message_handler = None,
                restclient = None):

        # populated initially via the login response
        self.seed_cap_url = seed_cap_url

        # the local proxy info, needed for building urls to send to the viewer
        self.proxy_host_ip = proxy_host_ip
        self.proxy_host_port = proxy_host_port

        # this is the ViewerProxyApp
        self.caller = caller

        # allow the message handler to be passed in
        # otherwise, just set one up
        if message_handler != None:
            self.message_handler = message_handler
        else:
            from pyogp.lib.base.message.message_handler import MessageHandler
            self.message_handler = MessageHandler()

        # we may in the future use something other than urllib2 (StdLibClient)
        if restclient == None:
            from pyogp.lib.base.network.stdlib_client import StdLibClient
            self.restclient = StdLibClient()
        else:
            self.restclient = restclient

        # stores the capability url <-> proxy uuid combo
        self.proxy_map = {}

        # stored the url:cap name map
        self.capability_map = {}

        # stores the event_queue info for parsing special data
        self.event_queue_client = EventQueueClient()
        self.event_queue_url = None

        # init the seed cap proxy
        self.add_proxy(self.seed_cap_url, 'seed_capability')

        logger.info("Initialized the CapabilitiesProxy for %s" %
                    (self.seed_cap_url))

    def start_caps_proxy_service(self):

        httpd = make_server(self.proxy_host_ip, self.proxy_host_port, self)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            sys.exit()
        except:
            traceback.print_exc()

    def add_proxy(self, url, capname):
        """ adds the url and it's proxy, and the proxy and it's url """

        # make available UUID <-> url dicts
        # we map each since the pairs are unique
        # and since we need to do lookups both ways (?)
        try:
            test = self.proxy_map[url]
        except KeyError:
            uuid = str(UUID().random())
            self.proxy_map[url] = uuid
            self.proxy_map[uuid] = url

            # store the url:capname
            self.capability_map[url] = capname

        return uuid

    def remove_proxy(self, proxied):
        """ removes the url and it's proxy, and the proxy and it's url """

        val = self.proxy_map[proxied]

        try:
            del self.proxy_map[proxied]
        except KeyError:
            pass

        try:
            del self.proxy_map[val]
            del self.capability_map[val]
        except KeyError:
            pass

    def swap_cap_urls(self, cap_map):
        """ takes the response to a seed_cap request for cap urls
        and maps proxy urls in place of the ones for the sim
        """

        # we expect a dict of {'capname':'url'}
        for cap in cap_map:

            # store the EventQueueGet url separately
            if cap == 'EventQueueGet':
                self.event_queue_url = cap_map[cap]
            cap_proxy_uuid = self.add_proxy(cap_map[cap], cap)
            cap_map[cap] = "http://%s:%s/%s" % (self.proxy_host_ip,
                                                self.proxy_host_port,
                                                cap_proxy_uuid)

            # store the url:capname
            self.capability_map[cap_map[cap]] = cap

        return cap_map

    def __call__(self, environ, start_response):
        """ handle a specific cap request and response using webob objects """

        self.environ = environ
        self.start = start_response
        self.request = Request(environ)
        self.response = Response()

        logger.info("Calling cap %s (%s) via %s with body of: %s" %
                    (self.capability_map[self.proxy_map[self.request.path[1:]]],
                    self.proxy_map[self.request.path[1:]],
                    self.request.method,
                    self.request.body))

        # urllib2 will return normally if the reponse status = 200
        # returns HTTPError if not
        # trap and send back to the viewer in either case
        try:

            if self.request.method=="GET":

                proxy_response = self.restclient.GET(self.proxy_map[self.request.path[1:]])

            elif self.request.method == "POST":

                proxy_response = self.restclient.POST(self.proxy_map[self.request.path[1:]],
                                                        self.request.body)

            logger.info("Cap %s (%s) responded with status %s and body of: %s" %
                        (self.capability_map[self.proxy_map[self.request.path[1:]]],
                        self.proxy_map[self.request.path[1:]],
                        proxy_response.status,
                        proxy_response.body))

            # build the webob.Response to send to the viewer
            status = proxy_response.status

            # if we are parsing the seed cap response, swap the cap urls
            # with our proxied ones
            if self.proxy_map[self.request.path[1:]] == self.seed_cap_url:

                cap_map = self.swap_cap_urls(llsd.parse(proxy_response.body))
                data = llsd.format_xml(cap_map)

            # if we are parsing the event queue, decode the data
            # this also runs it through the message_handler!
            # then curry it on out
            elif self.proxy_map[self.request.path[1:]] == self.event_queue_url:

                llsd_data = llsd.parse(proxy_response.body)

                self.event_queue_client._parse_result(llsd_data)

                # swap out child region ip:port with local proxies that we spin up
                if llsd_data.has_key('events'):

                    counter = 0

                    for item in llsd_data['events']:

                        # intercept EnableSimulator, start a UDPProxy instance for the sim_ip:port
                        # and swap values in the response to the client
                        if item['message'] == 'EnableSimulator':

                            # see pyogp.lib.client.agent.Agent().onEnableSimulator
                            target_ip = [ord(x) for x in item['body']['SimulatorInfo'][0]['IP']]
                            target_ip = '.'.join([str(x) for x in target_ip])
                            target_port = item['body']['SimulatorInfo'][0]['Port']

                            logger.debug("Handling EnableSimulator, spawning UDPProxy for: %s:%s" % (target_ip, target_port))

                            (local_ip, local_port)  = self.caller.start_udp_proxy(target_ip, target_port)

                            llsd_data['events'][counter]['body']['SimulatorInfo'][0]['IP'] = llsd.binary(''.join([chr(int(x)) for x in local_ip.split('.')]))
                            llsd_data['events'][counter]['body']['SimulatorInfo'][0]['Port'] = local_port

#                            data = llsd.format_xml(llsd_data)

                        # intercept EnableSimulator, start a UDPProxy instance for the sim_ip:port
                        # and swap values in the response to the client
                        elif item['message'] == 'EstablishAgentCommunication':

                            # Event Queue result from (None): {'events': [{'body': {'agent-id': UUID('a517168d-1af5-4854-ba6d-672c8a59e439'), 'sim-ip-and-port': '216.82.49.226:13002', 'seed-capability': 'https://sim3000.aditi.lindenlab.com:12043/cap/08bed841-54d3-f189-6566-dde97a0ba90c'}, 'message': 'EstablishAgentCommunication'}], 'id': 4}
                            sim_ip_and_port = item['body']['sim-ip-and-port']
                            sim_ip = sim_ip_and_port.split(':')[0]
                            port = sim_ip_and_port.split(':')[1]
                            seed_capability = item['body']['seed-capability']

                            # we know about this sim from EnableSimulator, pull it's ip port
                            proxied_sim_ip = self.caller.udp_proxied_hosts[(sim_ip, int(port))][0]
                            proxied_sim_port = self.caller.udp_proxied_hosts[(sim_ip, int(port))][1]

                            # spawn a new CapabilitiesProxy
                            (local_ip, local_port, path) = self.caller.start_caps_proxy(seed_capability)
                            proxied_seed_cap = "%s:%s/%s" % (local_ip, local_port, path)

                            logger.debug("Handling EstablishAgentCommunication, spawning CapabilitiesProxy for seed_cap: %s" % (seed_capability))
                            llsd_data['events'][counter]['body']['sim-ip-and-port'] = ':'.join([proxied_sim_ip, str(proxied_sim_port)])
                            llsd_data['events'][counter]['body']['seed-capability'] = proxied_seed_cap

#                            data = llsd.format_xml(llsd_data)

                        counter += 1

                    # skipping the above work for now, to work on something else.
                    data = proxy_response.body

            # otherwise, just proxy the data
            # normal caps go through no message_handler.
            # todo: fix the above (is a pyogp.lib.base fix)
            else:

                data = proxy_response.body

        # trap the HTTPError and build the appropriate response for the caller
        except HTTPError, error:
            status = error.code
            data = error.msg

        return self.send_response(status, data)


    def send_response(self, status, body=''):
        """ send the web response back to the caller """

        logger.debug("Sending cap response to viewer: Status:%s Body:%s" % (status, body))

        self.response.status = status
        self.response.body = body
        return self.response(self.environ, self.start)