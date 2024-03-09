#!/usr/bin/env python
# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
# fake - fake server for config and firmware
# Copyright (C) 2024  Chris Clark
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""To use this need to hack DNS somehow for your device, either the whole network or edit the /etc/hosts file


    # cat /etc/hosts
    127.0.0.1 localhost
    #192.168.1.1 uesmartradio.com
    #192.168.1.1 sn_not_configured
    # no https so http://config.logitechmusic.com works fine :-)
    192.168.1.1 config.logitechmusic.com


set FIRMWARE_FILENAME=baby_7.7.3_r16676.bin

Mar  2 10:21:59 squeezeplay: INFO   applet.SlimBrowser - SlimBrowserApplet.lua:3216 serverDisconnected() - connectedServer: false
Mar  2 10:21:59 squeezeplay: INFO   applet.SlimBrowser - SlimBrowserApplet.lua:3217 serverDisconnected() - attachedServer: nil
Mar  2 10:21:59 squeezeplay: INFO   net.comet - Comet.lua:1079 Comet {ID_mysqueezebox.com}: advice is retry, connect in 2.171 seconds
Mar  2 10:21:59 squeezeplay: INFO   applet.ConfigServer - ConfigServerApplet.lua:145 text    : Obligatory; Hack the planet! ;-)
Mar  2 10:21:59 squeezeplay: INFO   applet.ConfigServer - ConfigServerApplet.lua:146 service : www.mysqueezebox.com
Mar  2 10:21:59 squeezeplay: INFO   applet.ConfigServer - ConfigServerApplet.lua:147 firmware: http://127.0.01/baby_7.7.3_r16676.bin
Mar  2 10:21:59 squeezeplay: INFO   applet.ConfigServer - ConfigServerApplet.lua:148 prompt  : required
Mar  2 10:21:59 squeezeplay: INFO   applet.ConfigServer - ConfigServerApplet.lua:238 SN url to use: www.mysqueezebox.com
Mar  2 10:21:59 squeezeplay: INFO   applet.ConfigServer - ConfigServerApplet.lua:157 Upgrade required firmware without asking
Mar  2 10:21:59 squeezeplay: INFO   applet.SetupFirmware - UpgradeUBI.lua:266 /sbin/udevtrigger --subsystem-match=ubi
Mar  2 10:21:59 squeezeplay: INFO   applet.SetupFirmware - UpgradeUBI.lua:277 /sbin/udevsettle
Mar  2 10:22:00 squeezeplay: INFO   applet.SetupFirmware - UpgradeUBI.lua:400 Firmware url=http://127.0.01/baby_7.7.3_r16676.bin
Mar  2 10:22:00 squeezeplay: ERROR  net.http - SocketHttp.lua:390 SocketHttp {127.0.01}:t_sendRequest.pump: connection refused

"""

try:
    # Python 3.8 and later
    # py3
    from html import escape as escapecgi
except ImportError:
    # py2
    from cgi import escape as escapecgi

try:
    # py3
    from urllib.parse import parse_qs, parse_qsl
except ImportError:
    # py2 (and <py3.8)
    from cgi import parse_qs, parse_qsl
import os
try:
    import json
except ImportError:
    json = None
import logging
import mimetypes
import sys


from wsgiref.simple_server import make_server


try:
    import bjoern
except ImportError:
    bjoern = None

try:
    import meinheld  # https://github.com/mopemope/meinheld
except ImportError:
    meinheld = None

__version__ = '0.0.1'
DEFAULT_SERVER_PORT = 80
host_dir = os.path.abspath('.')

log = logging.getLogger(__name__)
logging.basicConfig()
log.setLevel(level=logging.DEBUG)


def to_bytes(in_str):
    # could choose to only encode for Python 3+
    return in_str.encode('utf-8')

def serve_file(start_response, path, content_type=None):  # Kinda mess API...
    """returns file type and file object, assumes file exists (and readable), returns [] for file on read error"""
    if content_type is None:
        content_type = mimetypes.guess_type(path)[0]  # over kill for this tool/hack
    try:
        #f = open(path, 'rb')  # for supporting streaming
        fp = open(path, 'rb')
        f = [fp.read()]  # hack so we can get length at expensive of no streaming and reading entire file in to memory
        fp.close()
    except IOError:
        f = []
    log.debug('content_type %r', content_type)
    status = '200 OK'
    headers = [('Content-type', content_type)]
    start_response(status, headers)
    return f
    #return to_bytes(content_type), f

def not_found(environ, start_response):
    """serves 404s."""
    #start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
    #return ['Not Found']
    start_response('404 NOT FOUND', [('Content-Type', 'text/html')])
    return [to_bytes('''<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL /??????? was not found on this server.</p>
</body></html>''')]

def simple_app(environ, start_response):
    print('')  # newline to seperate calls
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]
    result= []

    path_info = environ['PATH_INFO']

    # Returns a dictionary in which the values are lists
    if environ.get('QUERY_STRING'):
        get_dict = parse_qs(environ['QUERY_STRING'])
    else:
        get_dict = {}  # wonder if should make None to make clear its not there at all

    # dump out information about request
    #print(environ)
    #pprint(environ)
    print('PATH_INFO %r' % environ['PATH_INFO'])
    print('CONTENT_TYPE %r' % environ.get('CONTENT_TYPE'))  # missing under bjoern
    print('QUERY_STRING %r' % environ.get('QUERY_STRING'))  # missing under bjoern
    print('QUERY_STRING dict %r' % get_dict)
    print('REQUEST_METHOD %r' % environ['REQUEST_METHOD'])
    #print('environ %r' % environ) # DEBUG, potentially pretty print, but dumping this is non-default
    #print('environ:') # DEBUG, potentially pretty print, but dumping this is non-default
    #pprint(environ, indent=4)
    print('Filtered headers, HTTP*')
    for key in environ:
        if key.startswith('HTTP_'):  # TODO potentially startswith 'wsgi' as well
            # TODO remove leading 'HTTP_'?
            print('http header ' + key + ' = ' + repr(environ[key]))


    if environ['PATH_INFO'] == '/firmware.bin':
        return serve_file(start_response, os.environ.get('FIRMWARE_FILENAME', 'firmware.bin'))
    else:
        # just ignore the request for now and ALWAYS return json payload
        # TODO handle one special case, the firware download request
        status = '200 OK'
        headers = [('Content-type', 'application/json')]
        result = []
        fake_firmware_upgrade = {
            "channel":{"text":"Obligatory; Hack the planet! ;-)","service":"www.mysqueezebox.com"},
            "firmware":{
                "version":"7.7.3 r16676",
                "prompt":"required",
                #"url":"http://127.0.01/baby_7.7.3_r16676.bin"  # TODO see above TODO note
                "url":"http://config.logitechmusic.com/firmware.bin"  # TODO see above TODO note
            }
        }

        result.append(json.dumps(fake_firmware_upgrade, indent=4, default=str).encode('utf-8'))
    start_response(status, headers)
    return result

def determine_local_ipaddr():
    return '127.0.0.1'  # FIXME

def main(argv=None):
    print('Python %s on %s' % (sys.version, sys.platform))
    server_port = int(os.environ.get('PORT', DEFAULT_SERVER_PORT))

    print("Serving on port %d..." % server_port)
    local_ip = os.environ.get('LISTEN_ADDRESS', determine_local_ipaddr())
    log.info('Starting server: %r', (local_ip, server_port))
    if bjoern:
        log.info('Using: bjoern')
        bjoern.run(simple_app, '', server_port)  # FIXME use local_ip?
    elif meinheld:
        # Untested, Segmentation fault when serving a file :-(
        meinheld.server.listen(('0.0.0.0', server_port))  # does not accept ''
        meinheld.server.run(simple_app)
    else:
        log.info('Using: wsgiref.simple_server')
        httpd = make_server('', server_port, simple_app)  # FIXME use local_ip?
        httpd.serve_forever()

if __name__ == "__main__":
    sys.exit(main())
