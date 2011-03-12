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

from qrcan_exceptions import *
from qrcan_store import *

class QrcanAPI:
	
	DATASOURCES_METADATA_BASE = 'datasources'
	
	def __init__(self):
		self.datasources = Graph()
		self.dslist = list()
		self.store = QrcanStore()
		self.apimap = {
				'/api/datasource/all' : 'list_all_datasources',
				'/api/datasource' : 'update_datasource',
				'/api/query' : 'query_datasource'
		}
		
	def dispatch_api_call(self, noun, instream, outstream, headers):
		try:
			m = getattr(self, self.apimap[str(noun)]) # handling fixed resources
			m(instream, outstream, headers)
		except KeyError: # handling potentially dynamic resources
			if noun.startswith('/api/datasource/'):
				try:
					self._serve_ds_description(outstream, noun.split("/")[-1])
				except DatasourceNotExists:
					_logger.debug('data source does not exist')
					raise HTTP404
			else:
				_logger.debug('unknown noun %s' %noun)
				raise HTTP404

	def init_datasources(self):
		_logger.debug('scanning [%s] for data sources ...' %QrcanAPI.DATASOURCES_METADATA_BASE)
		for f in os.listdir(QrcanAPI.DATASOURCES_METADATA_BASE):
			if f.endswith('.ttl'):
				self.datasources.parse(''.join([QrcanAPI.DATASOURCES_METADATA_BASE, '/', f]), format='n3')
		self.dslist = self._generate_datasource_list()
		
	def list_all_datasources(self, instream, outstream, headers):
		outstream.write(json.JSONEncoder().encode(self.dslist))

	def query_datasource(self, instream, outstream, headers):
		_logger.debug("query ds")
		res = self.store.query_datasource('http://localhost:6969/api/datasource/michaelsfoaffile', 'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?label WHERE { ?s rdfs:label ?label }')
		for r in res:
			outstream.write(str(r))
		
	def update_datasource(self, instream, outstream, headers):
		dsdata = self._get_formenc_param(instream, headers, 'dsdata')
		if dsdata:
			_logger.info('Creating data source with following characteristics:')
			for key in dsdata.keys():
				_logger.info('%s = %s' %(key, dsdata[key]))
			space_id = self._create_ds_description(dsdata['id'], dsdata['name'], dsdata['access_method'], dsdata['access_uri'], dsdata['access_mode'])
			self.store.add_datasource_doc(space_id, dsdata['access_uri'])
		else:
			_logger.info('Creating stub data source due to insufficient information provided.')
		self.init_datasources()

	def _serve_ds_description(self, outstream, ds_id):
		ds_desc = ''.join(['http://localhost:6969/api/datasource/', ds_id)
		if ds_id in self.dslist

		except KeyError:
		  raise DatasourceNotExists
		outstream.write(json.JSONEncoder().encode(self._get_ds(ds)))

	def _get_formenc_param(self, instream, headers, param):
		encparams = instream.read(int(headers.getheader('content-length')))
		params = cgi.parse_qs(encparams)
		if params[param]:
			params = json.JSONDecoder().decode(params[param][0])
			return params
		else:
			return None