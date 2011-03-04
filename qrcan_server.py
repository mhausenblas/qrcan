#!/usr/bin/env python
# encoding: utf-8
"""
qrcan_server.py

Created by Michael Hausenblas on 2011-03-04.
"""

import sys	
import BaseHTTPServer
import SimpleHTTPServer
import qrcan_api
from optparse import OptionParser

QRCAN_DEFAULT_PORT = 6969

class QrcanWebHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
	def do_GET(self):
		if self.path.startswith("/api"):
			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self.end_headers()
			qrcanapi = qrcan_api.QrcanAPI(self.wfile)
			qrcanapi.dispatch_api_call(self.path)
			return self
		else:
			if self.path.startswith("/ui"):
				return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
			else: 
				self.send_error(404)

if __name__ == '__main__':
	parser = OptionParser()
	parser.set_usage('%prog [options] ')
	parser.add_option('-p', '--port', dest = 'port', help = 'The port qrcan should listen on, defaults to %s' %QRCAN_DEFAULT_PORT)
	(options, args) = parser.parse_args()

	port = QRCAN_DEFAULT_PORT

	if options.port:
		try:
			port = int(options.port)
			if not ( 0 < port < 65536 ):
				raise ValueError()
		except ValueError:
			parser.error('The port number has to be numeric, between 1 and 65535)')
	
	httpd = BaseHTTPServer.HTTPServer(('', port), QrcanWebHandler)
	print "qrcan server running on port %s" %port
  
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		print 'The qrcan server was terminated on user request. Thanks for using qrcan!'