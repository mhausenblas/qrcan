#!/usr/bin/env python
# encoding: utf-8
"""
qrcan_api.py

Created by Michael Hausenblas on 2011-03-04.
"""
import logging
_logger = logging.getLogger('qrcan')

import sys
import os
import rdflib
import cgi
import datetime
try:
    import json
except ImportError:
    import simplejson as json
from rdflib import Graph
from rdflib import Namespace
from rdflib import URIRef
from rdflib import Literal
from rdflib import RDF
from rdflib import XSD

from qrcan_ds import *
from qrcan_exceptions import *
from qrcan_store import *

class QrcanAPI:
	# HTTP API configuration:
	API_BASE = '/api'
	DATASOURCES_API_BASE = '/datasource'
	# Configuration of the data source description store:
	DATASOURCES_METADATA_BASE = 'datasources/'
	
	def __init__(self, api_base):
		self.datasources = dict()
		self.api_base = api_base
		self.datasource_base = ''.join([api_base, QrcanAPI.API_BASE, QrcanAPI.DATASOURCES_API_BASE, '/'])
		self.store = QrcanStore()
		self.apimap = {
				''.join([QrcanAPI.API_BASE, QrcanAPI.DATASOURCES_API_BASE, '/all']) : 'list_all_datasources', # GET
				''.join([QrcanAPI.API_BASE, QrcanAPI.DATASOURCES_API_BASE]) : 'add_datasource'                # POST
		}
		_logger.debug('API ready at %s' %''.join([api_base, QrcanAPI.API_BASE]))
		
	def dispatch_api_call(self, noun, instream, outstream, headers):
		try:
			m = getattr(self, self.apimap[str(noun)]) # handling fixed resources
			m(instream, outstream, headers)
		except KeyError: # handling potentially dynamic resources
			if noun.startswith(''.join([QrcanAPI.API_BASE, QrcanAPI.DATASOURCES_API_BASE, '/'])):
				try:
					dsid = ''.join([self.api_base, noun])
					_logger.debug('Target data source [%s]' %dsid)
					if dsid.endswith('/'): # POST
						dsid = dsid[:-1] # remove the trailing slash
						self._update_datasource(instream, outstream, headers, dsid)
					else: # GET
						self._serve_datasource(outstream, dsid)
				except DatasourceNotExists:
					_logger.debug('Seems the data source does not exist!')
					raise HTTP404
			else:
				_logger.debug('unknown noun %s' %noun)
				raise HTTP404

	def init_datasources(self):
		_logger.debug('Scanning [%s] for data sources ...' %QrcanAPI.DATASOURCES_METADATA_BASE)
		for f in os.listdir(QrcanAPI.DATASOURCES_METADATA_BASE):
			if f.endswith('.ttl'):
				ds = Datasource(self.datasource_base, QrcanAPI.DATASOURCES_METADATA_BASE)
				ds.load(''.join([QrcanAPI.DATASOURCES_METADATA_BASE, f]))
				self.datasources[ds.identify()] = ds
				_logger.debug('Added data sources [%s]' %ds.identify())

	def list_all_datasources(self, instream, outstream, headers):
		dslist = list()
		for ds in self.datasources.itervalues():
			dslist.append(ds.describe(encoding = 'raw'))
		outstream.write(json.JSONEncoder().encode(dslist))
		
	def add_datasource(self, instream, outstream, headers):
		dsdata = self._get_formenc_param(instream, headers, 'dsdata')
		if dsdata:
			_logger.debug('Creating data source with:')
			for key in dsdata.keys():
				_logger.debug('%s = %s' %(key, dsdata[key]))
			ds = Datasource(self.datasource_base, QrcanAPI.DATASOURCES_METADATA_BASE)
			ds.update(dsdata['name'], dsdata['access_method'], dsdata['access_uri'], dsdata['access_mode'])
			ds.store()
			self.datasources[ds.identify()] = ds

	def _serve_datasource(self, outstream, dsid):
		_logger.debug('Trying to get description of data source [%s] ...' %dsid)
		try:
			ds = self.datasources[dsid]
			outstream.write(ds.describe())
		except KeyError:
			raise DatasourceNotExists

	def _update_datasource(self, instream, outstream, headers, dsid):
		dsdata = self._get_formenc_param(instream, headers, 'dsdata')
		if dsdata:
			_logger.debug('Updating data source with:')
			for key in dsdata.keys():
				_logger.debug('%s = %s' %(key, dsdata[key]))
			try:
				self.datasources[dsid].update(dsdata['name'], dsdata['access_method'], dsdata['access_uri'], dsdata['access_mode'])
				self.datasources[dsid].store()
			except KeyError:
				raise DatasourceNotExists

	def _get_formenc_param(self, instream, headers, param):
		encparams = instream.read(int(headers.getheader('content-length')))
		params = cgi.parse_qs(encparams)
		if params[param]:
			params = json.JSONDecoder().decode(params[param][0])
			return params
		else:
			return None