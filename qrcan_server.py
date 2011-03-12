#!/usr/bin/env python
# encoding: utf-8
"""
qrcan_server.py

Created by Michael Hausenblas on 2011-03-04.
"""

import logging
_logger = logging.getLogger('qrcan')
_logger.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter('%(name)s %(levelname)s: %(message)s'))
_logger.addHandler(_handler)

import sys
import BaseHTTPServer
import SimpleHTTPServer
import urlparse
import qrcan_api
from qrcan_exceptions import *
from optparse import OptionParser

QRCAN_DEFAULT_PORT = 6969
QRCAN_HOST = 'http://localhost'

class QrcanWebHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
	qrcanapi = qrcan_api.QrcanAPI(''.join([QRCAN_HOST, ':', str(QRCAN_DEFAULT_PORT)]))
	qrcanapi.init_datasources()
	
	def do_GET(self):
		if self.path.startswith("/api"):
			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self.end_headers()
			try:
				QrcanWebHandler.qrcanapi.dispatch_api_call(self.path, self.rfile, self.wfile, self.headers)
			except HTTP404:
				_logger.warning('unsupported API call')
				self.send_error(404)
			else:
				return self
		else:
			if self.path.startswith("/ui"):
				return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
			else: 
				_logger.warning('neither UI nor API call')
				self.send_error(404)

	def do_POST(self):
		if self.path.startswith("/api"):
			self.send_response(201)
			self.end_headers()
			QrcanWebHandler.qrcanapi.dispatch_api_call(self.path, self.rfile, self.wfile, self.headers)
		else:
			self.send_error(404)



if __name__ == '__main__':
	#parser = OptionParser()
	#parser.set_usage('%prog [options] ')
	#parser.add_option('-p', '--port', dest = 'port', help = 'The port qrcan should listen on, defaults to %s' %QRCAN_DEFAULT_PORT)
	#(options, args) = parser.parse_args()

	#if options.port:
	#	try:
	#		port = int(options.port)
	#		if not ( 0 < port < 65536 ):
	#			raise ValueError()
	#	except ValueError:
	#		parser.error('The port number has to be numeric, between 1 and 65535)')
	
	httpd = BaseHTTPServer.HTTPServer(('', QRCAN_DEFAULT_PORT), QrcanWebHandler)
	print '-'*40
	print 'qrcan server running on port %s ...' %QRCAN_DEFAULT_PORT
	print '-'*40
 
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		print 'The qrcan server was terminated on user request. Thanks for using qrcan!'