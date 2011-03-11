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

rdflib.plugin.register('sparql', rdflib.query.Processor, 'rdfextras.sparql.processor', 'Processor')
rdflib.plugin.register('sparql', rdflib.query.Result, 'rdfextras.sparql.query', 'SPARQLQueryResult')

class QrcanAPI:
	NAMESPACES = {	'void' : Namespace('http://rdfs.org/ns/void#'),
					'dcterms' : Namespace('http://purl.org/dc/terms/'),
					'qrcan' : Namespace('http://vocab.deri.ie/qrcan#')
					
	}
	
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
		self.dslist = self._get_ds(self.datasources)
		for ds in self.dslist:
			_logger.debug('loading %s' %ds['id'])
		
	def query_datasource(self, instream, outstream, headers):
		_logger.debug("query ds")
		res = self.store.query_datasource('http://localhost:6969/api/datasource/michaelsfoaffile', 'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?label WHERE { ?s rdfs:label ?label }')
		for r in res:
			outstream.write(str(r))
		
	def list_all_datasources(self, instream, outstream, headers):
		outstream.write(json.JSONEncoder().encode(self.dslist))

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
				
	def _get_formenc_param(self, instream, headers, param):
		encparams = instream.read(int(headers.getheader('content-length')))
		params = cgi.parse_qs(encparams)
		if params[param]:
			params = json.JSONDecoder().decode(params[param][0])
			return params
		else:
			return None

	def _serve_ds_description(self, outstream, ds_id):
		ds_desc = ''.join([QrcanAPI.DATASOURCES_METADATA_BASE, '/', ds_id, '.ttl'])
		try:
			ds_file = open(ds_desc, 'r')
		except IOError:
		  raise DatasourceNotExists
		else:
			ds = Graph()
			ds.parse(ds_desc, format='n3')
			outstream.write(json.JSONEncoder().encode(self._get_ds(ds)))
	
	
	def _create_ds_description(self, ds_id, name, access_method, access_uri, access_mode):
		if ds_id.startswith('http://'):
			ds_id = ds_id.split("/")[-1]
			
		#create an extended VoID description of the data source
		ds = URIRef('http://localhost:6969/api/datasource/' + str(ds_id))
		ds_graph = Graph()
		ds_graph.add((ds, RDF.type,  QrcanAPI.NAMESPACES['void']['Dataset']))
		ds_graph.add((ds, QrcanAPI.NAMESPACES['dcterms']['title'], Literal(name)))
		if(access_method == 'doc'):
			ds_graph.add((ds, QrcanAPI.NAMESPACES['void']['dataDump'], URIRef(access_uri)))
		else:
			ds_graph.add((ds, QrcanAPI.NAMESPACES['void']['sparqlEndpoint'], URIRef(access_uri)))
		ds_graph.add((ds, QrcanAPI.NAMESPACES['qrcan']['mode'], URIRef(str(QrcanAPI.NAMESPACES['qrcan'] + access_mode))))
		ds_graph.add((ds, QrcanAPI.NAMESPACES['dcterms']['modified'], Literal(datetime.datetime.utcnow())))
		
		# store VoID description:
		ds_graph.bind('void', QrcanAPI.NAMESPACES['void'], True)
		ds_graph.bind('dcterms', QrcanAPI.NAMESPACES['dcterms'], True)
		ds_graph.bind('qrcan', QrcanAPI.NAMESPACES['qrcan'], True)
		ds_file = open(''.join([QrcanAPI.DATASOURCES_METADATA_BASE, '/', ds_id, '.ttl']), 'w')
		ds_file.write(ds_graph.serialize(format='n3'))
		ds_file.close()
		return str(ds)
		
	def _get_ds(self, graph):
		dslist = list()
		querystr = 'SELECT * WHERE { ?ds a void:Dataset ; dcterms:title ?title; qrcan:mode ?accessMode . OPTIONAL { ?ds void:dataDump ?dumpURI . } OPTIONAL { ?ds void:sparqlEndpoint ?sparqlURI . } }'
		res = graph.query(querystr, initNs=QrcanAPI.NAMESPACES)
		for r in res.bindings:
			if r['ds']:
				ds = r['ds']
				#_logger.debug(ds)
			if r['title']: title = r['title']
			try:
				if r['dumpURI']:
					access_uri = r['dumpURI']
					access_method = 'doc'
			except KeyError:
				pass
			try:
				if r['sparqlURI']:
					access_uri = r['sparqlURI']
					access_method = 'sparql'
			except KeyError:
				pass
			if r['accessMode']:
				if str(r['accessMode']) == 'http://vocab.deri.ie/qrcan#remote':
					access_mode = 'remote'
				else:
					access_mode = 'local'
			
			dslist.append({ 'id' : ds, 'name' : title, 'access_method' : access_method, 'access_uri' : access_uri, 'access_mode' : access_mode })
		return dslist