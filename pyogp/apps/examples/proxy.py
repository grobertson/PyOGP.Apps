
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

import re
from webob import Request, Response
from wsgiref.simple_server import make_server
import xmlrpclib
import urllib2

from indra.base import llsd

from pyogp.lib.base.network.stdlib_client import StdLibClient, HTTPError
from pyogp.lib.client.login import Login

# initialize globals
logger = getLogger('pyogp.lib.client.login')
DEBUG = 1

class LoginProxy(object):
    """ """

    def __init__(self, loginuri, restclient = None):

        self.loginuri = loginuri
        self.login_handler = Login()

        if restclient == None: 
            self.restclient = StdLibClient() 
        else:
            self.restclient = restclient

        print "Initialized the login proxy for %s" % self.loginuri

    def __call__(self, environ, start_response):

        self.environ = environ
        self.start = start_response

        self.request = Request(environ)

        self.response = Response()

        try:
            login_params = xmlrpclib.loads(self.request.body)

            response = self.login_handler._post_to_legacy_loginuri(self.loginuri, login_params = login_params[0][0], login_method = login_params[1], proxied = True)

            print response['sim_ip']
            print response['sim_port']
            print response['seed_capability']

            tuple_response = tuple([response])
            self.response.body = xmlrpclib.dumps(tuple_response)

            return self.response(environ, start_response)

        except Exception, e:
            #start_response('404', [('Content-Type', 'text/html')])
            print e

            return self.response(environ, start_response)

def main():

    print "i'm only proxying logins right now, stay tuned for more fun soon!"

    import optparse

    parser = optparse.OptionParser(
        usage='%prog --port=PORT'
        )
    parser.add_option(
        '-p', '--port',
        default='8080',
        dest='port',
        type='int',
        help='Port to serve on (default 8080)')
    parser.add_option(
        '--loginuri',
        default='https://login.aditi.lindenlab.com/cgi-bin/login.cgi',
        dest='loginuri',
        help='Specifies the target loginuri to connect proxy to')

    options, args = parser.parse_args()

    app = LoginProxy(options.loginuri)

    httpd = make_server('localhost', options.port, app)

    print 'Serving login requests on https://localhost:%s' % options.port

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print '^C'

if __name__=="__main__":
    main()

