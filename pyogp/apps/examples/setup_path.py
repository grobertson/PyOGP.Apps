import sys
import os

source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/'))
eggs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../eggs/'))

try:
    indra_dir = os.path.abspath(
        os.path.dirname(
        os.path.dirname(
        os.path.dirname(
        os.path.realpath(__file__)))))

    lib_dir = os.path.join(indra_dir, 'lib', 'python')
    print lib_dir
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)

    try:

        import indra.base
        import uuid
        import pyogp.lib.base
        import eventlet
        import elementtree
        import indra.util

    except ImportError, error:
        print "A required module cannot be imported: %s" % (error)
        sys.exit()

except:
    # test to see if we are in a built buildout context
    if os.path.exists(source_dir) and os.path.exists(eggs_dir):

        source_path = os.path.abspath(source_dir)
        eggs_path = os.path.abspath(eggs_dir)

        # if we have built, then there will be items in these directories
        if len(os.listdir(source_path)) > 1 and len(os.listdir(eggs_path)) > 1:

            # append everythin in the built out dirs to the path
            try: 
                [sys.path.append(os.path.join(source_path, package)) for package in os.listdir(source_path) if not package == '.svn' and not package == 'EXTERNALS.txt'] 
                [sys.path.append(os.path.join(eggs_path, package)) for package in os.listdir(eggs_path) if not package == '.svn' and not package == 'EXTERNALS.txt']

            except Exception, error:
                print "Failed to append the required modules to the path. Have you run buildout yet?"
                sys.exit()

        else:
            print "Failed to append the required modules to the path. Have you run buildout yet?"
            sys.exit()           

    else:

        # we haven't run buildout and need to see if we can simply import the required modules

        try:

            import indra.base
            import uuid
            import pyogp.lib.base
            import eventlet
            import elementtree
            import indra.util

        except ImportError, error:
            print "A required module cannot be imported: %s" % (error)
            sys.exit()

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
