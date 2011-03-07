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
try:
    import json
except ImportError:
    import simplejson as json
from rdflib import Graph
from rdflib import Namespace
from rdflib import URIRef
from rdflib import Literal
from rdflib import RDF
from qrcan_exceptions import *

rdflib.plugin.register('sparql', rdflib.query.Processor, 'rdfextras.sparql.processor', 'Processor')
rdflib.plugin.register('sparql', rdflib.query.Result, 'rdfextras.sparql.query', 'SPARQLQueryResult')

class QrcanAPI:
	NAMESPACES = {	'void' : Namespace('http://rdfs.org/ns/void#'),
					'dcterms' : Namespace('http://purl.org/dc/terms/'),
					'qrcan' : Namespace('http://vocab.deri.ie/qrcan#')
					
	}
	
	def __init__(self, instream, outstream, headers):
		self.datasources = Graph()
		self.instream = instream
		self.outstream = outstream
		self.headers = headers
		self.apimap = {
				'/api/datasource/all' : 'list_all_datasets',
				'/api/datasource' : 'update_dataset'
		}
		
	def dispatch_api_call(self, noun):
		try:
			m = getattr(self, self.apimap[str(noun)]) # handling fixed resources
			m()
		except KeyError: # handling potentially dynamic resources
			if noun.startswith('/api/datasource/'):
				try:
					self._serve_ds_description(noun.split("/")[-1])
				except DatasourceNotExists:
					_logger.debug('data source does not exist')
					raise HTTP404
			else:
				_logger.debug('unknown noun %s' %noun)
				raise HTTP404

	def list_all_datasets(self):
		for f in os.listdir('datasources'):
			if f.endswith('.ttl'):
				self.datasources.parse('datasources/' + f, format='n3')
		dslist = self._get_ds(self.datasources)
		self.outstream.write(json.JSONEncoder().encode(dslist))

	def update_dataset(self):
		dsdata = self._get_formenc_param('dsdata')
		if dsdata:
			self.outstream.write('Creating data source with following characteristics: <br />')
			for key in dsdata.keys():
				self.outstream.write('%s = %s <br />' %(key, dsdata[key]))
			self._create_ds_description(dsdata['id'], dsdata['name'], dsdata['access_method'], dsdata['access_uri'], dsdata['access_mode'])
		else:
				self.outstream.write('Creating stub data source due to insufficient information provided.')
			
				
	def _get_formenc_param(self, param):
		encparams = self.instream.read(int(self.headers.getheader('content-length')))
		params = cgi.parse_qs(encparams)
		if params[param]:
			params = json.JSONDecoder().decode(params[param][0])
			return params
		else:
			return None

	def _serve_ds_description(self, ds_id):
		ds_desc = ''.join(['datasources/', ds_id, '.ttl'])
		try:
			ds_file = open(ds_desc, 'r')
		except IOError:
		  raise DatasourceNotExists
		else:
			ds = Graph()
			ds.parse(ds_desc, format='n3')
			self.outstream.write(json.JSONEncoder().encode(self._get_ds(ds)))
	
	
	def _create_ds_description(self, ds_id, name, access_method, access_uri, access_mode):
		void_dataset = QrcanAPI.NAMESPACES['void']['Dataset']
		ds = URIRef('http://localhost:6969/api/datasource/' + str(ds_id))
		ds_graph = Graph()
		ds_graph.add((ds, RDF.type, void_dataset))
		ds_graph.add((ds, QrcanAPI.NAMESPACES['dcterms']['title'], Literal(name)))
		ds_graph.add((ds, QrcanAPI.NAMESPACES['void']['dataDump'], URIRef(access_uri)))
		ds_graph.add((ds, QrcanAPI.NAMESPACES['qrcan']['mode'], URIRef(str(QrcanAPI.NAMESPACES['qrcan'] + access_mode))))
		
		# store VoID description:
		ds_graph.bind('void', QrcanAPI.NAMESPACES['void'], True)
		ds_graph.bind('dcterms', QrcanAPI.NAMESPACES['dcterms'], True)
		ds_graph.bind('qrcan', QrcanAPI.NAMESPACES['qrcan'], True)
		ds_file = open(''.join(['datasources/', ds_id, '.ttl']), 'w')
		ds_file.write(ds_graph.serialize(format='n3'))
		ds_file.close()
		
	def _get_ds(self, graph):
		dslist = list()
		querystr = 'SELECT * WHERE { ?ds a void:Dataset ; dcterms:title ?title . OPTIONAL { ?ds void:dataDump ?dump; } }'
		res = graph.query(querystr, initNs=QrcanAPI.NAMESPACES)
		for r in res.bindings:
			_logger.debug(r)
			if r['ds']: ds = r['ds']
			if r['title']: title = r['title']
			if r['dump']: dump = r['dump']
			dslist.append({ 'id' : ds, 'name' : title, 'access_uri' : dump })
		return dslist