#!/usr/bin/env python
# encoding: utf-8
"""
qrcan_ds.py

Defines the handling of data source descriptions.

Created by Michael Hausenblas on 2011-03-12.
"""
import logging
_logger = logging.getLogger('qrcan')

import sys
import os
import uuid
import rdflib
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
from rdfextras.sparql.query import SPARQLQueryResult
from rdflib.plugin import PluginException
from SPARQLWrapper import SPARQLWrapper, JSON

rdflib.plugin.register('sparql', rdflib.query.Processor, 'rdfextras.sparql.processor', 'Processor')
rdflib.plugin.register('sparql', rdflib.query.Result, 'rdfextras.sparql.query', 'SPARQLQueryResult')

from qrcan_exceptions import *

class Datasource:
	"""A data source
	
	Represents a data source in qrcan, including loading from/storing 
	to a file using VoID and other vocabualries to persist the state.
	"""
	ACCESS_DOCUMENT = 'doc'
	ACCESS_SPARQL_ENDPOINT = 'sparql'
	MODE_REMOTE = 'remote'
	MODE_LOCAL = 'local'
	NAMESPACES = {	'void' : Namespace('http://rdfs.org/ns/void#'),
					'dcterms' : Namespace('http://purl.org/dc/terms/'),
					'qrcan' : Namespace('http://vocab.deri.ie/qrcan#')
					
	}
	
	def __init__(self, base_uri, store_dir):
		"""Inits the data source.

		The base_uri is used for generating the data source ID and  
		store_dir is the relative directory used for making the
		data source persistent, for example:
		
		Datasource('http://example.org/', 'datasources/')
		"""
		tmp_id = str(uuid.uuid1())
		self.g = Graph()
		if base_uri.endswith('/'): 
			self.base_uri = base_uri
		else:
			self.base_uri = ''.join([base_uri, '/']) 
		if store_dir.endswith('/'): 
			self.file_name = ''.join([store_dir, tmp_id, '.ttl'])
		else:
			self.file_name = ''.join([store_dir, '/', tmp_id, '.ttl'])
		self.id = ''.join([self.base_uri, tmp_id])
		self.name = ''
		self.updated = datetime.datetime.utcnow()
		self.access_method = Datasource.ACCESS_DOCUMENT
		self.access_uri = ''
		self.access_mode = Datasource.MODE_REMOTE
		self.last_sync = None
		self.g.bind('void', Datasource.NAMESPACES['void'], True)
		self.g.bind('dcterms', Datasource.NAMESPACES['dcterms'], True)
		self.g.bind('qrcan', Datasource.NAMESPACES['qrcan'], True)

	def identify(self):
		"""Returns the ID of the data source as string.
		"""
		return str(self.id)
		
	def sync_status(self):
		"""Returns the synchronisation status of the data source.
		
		False if not yet synced, a UTC-based date-time stamp string of last sync otherwise.
		"""
		if self.last_sync:
			return str(self.last_sync)
		else:
			return False

	def location(self):
		"""Returns the path to the VoID file where the data source is made persistent.
		"""
		return self.file_name
		
	def load(self, file_name):
		"""Loads the data source description from a VoID file.
		"""
		self.file_name = file_name
		self.g.parse(self.file_name, format='n3')
		querystr = """	SELECT * 
						WHERE { 
							?ds a void:Dataset ; 
								dcterms:title ?title; 
								dcterms:modified ?modified; 
								qrcan:mode ?accessMode . 
								OPTIONAL { ?ds void:dataDump ?dumpURI . } 
								OPTIONAL { ?ds void:sparqlEndpoint ?sparqlURI . }
								OPTIONAL { ?ds qrcan:synced ?lastSync . } 
						}
		"""
		res = self.g.query(querystr, initNs=Datasource.NAMESPACES)
		for r in res.bindings:
			if r['ds']: self.id = r['ds']
			if r['title']: self.name = r['title']
			if r['modified']: self.updated = r['modified']
			try:
				if r['dumpURI']:
					self.access_uri = r['dumpURI']
					self.access_method = Datasource.ACCESS_DOCUMENT
			except KeyError:
				pass
			try:
				if r['sparqlURI']:
					self.access_uri = r['sparqlURI']
					self.access_method = Datasource.ACCESS_SPARQL_ENDPOINT
			except KeyError:
				pass
			if r['accessMode']:
				if 'remote' in str(r['accessMode']):
					self.access_mode = Datasource.MODE_REMOTE
				else:
					self.access_mode = Datasource.MODE_LOCAL
			try:
				if r['lastSync']:
					self.last_sync = r['lastSync']
			except KeyError:
				pass
	
	def store(self):
		"""Stores the data source description to a VoID file.
		"""
		ds_file = open(self.file_name, 'w')
		ds_file.write(self.g.serialize(format='n3'))
		ds_file.close()

	def update(self, name, access_method, access_uri, access_mode):
		"""Updates a description of the data source.
		"""
		self.name = name
		self.updated = datetime.datetime.utcnow()
		self.access_method = access_method
		self.access_uri = access_uri
		self.access_mode = access_mode

		# update the graph as well:
		self.g.set((URIRef(self.id), RDF.type, Datasource.NAMESPACES['void']['Dataset']))
		self.g.set((URIRef(self.id), Datasource.NAMESPACES['dcterms']['title'], Literal(self.name)))
		self.g.set((URIRef(self.id), Datasource.NAMESPACES['dcterms']['modified'], Literal(self.updated)))
		if(self.access_method == Datasource.ACCESS_DOCUMENT):
			self.g.set((URIRef(self.id), Datasource.NAMESPACES['void']['dataDump'], URIRef(self.access_uri)))
		else:
			self.g.set((URIRef(self.id), Datasource.NAMESPACES['void']['sparqlEndpoint'], URIRef(self.access_uri)))
		self.g.set((URIRef(self.id), Datasource.NAMESPACES['qrcan']['mode'], URIRef(str(Datasource.NAMESPACES['qrcan'] + self.access_mode))))
		if self.sync_status(): # only remember if synced
			if self.access_mode == Datasource.MODE_LOCAL:
				self.g.set((URIRef(self.id), Datasource.NAMESPACES['qrcan']['synced'], Literal(self.last_sync)))
			else:
				self.g.remove((URIRef(self.id), Datasource.NAMESPACES['qrcan']['synced'], None))
		
	def describe(self, format = 'json', encoding = 'str'):
		"""Creates a description of the data source.

		The format parameter determines the resulting description format:
		'json' produces a JSON object and 'rdf' an RDF/Turtle string.
		If encoding is set to 'raw', the respective object is returned,
		if set to 'str', an string-encoded version is returned.  
		"""
		if format == 'json':
			ds = {	'id' : self.id, 
					'name' : self.name,
					'updated' : str(self.updated),
					'access_method' : self.access_method,
					'access_uri' : self.access_uri,
					'access_mode' : self.access_mode
			}
			if self.access_mode == Datasource.MODE_LOCAL and sync_status():
				ds['last_sync'] =  str(self.last_sync)
			if encoding == 'str':
				return json.JSONEncoder().encode(ds)
			else:
				return ds
				
		if format == 'rdf':
			if encoding == 'str':
				return str(self.g.serialize(format='n3'))
			else:
				return self.g

	def sync(self, g):
		"""Synchronises a local data sources into a graph.
		
		For local data sources - updates the last_sync field.
		Remote data sources are not effected.
		"""
		if self.access_mode == Datasource.MODE_LOCAL and self.access_method == Datasource.ACCESS_DOCUMENT: # restrict to RDF documents for now
			try:
				self._load_from_file(g)
				self.last_sync = datetime.datetime.utcnow()
				self.g.set((URIRef(self.id), Datasource.NAMESPACES['qrcan']['synced'], Literal(self.last_sync)))
			except DatasourceLoadError:
				_logger.debug('Sync failed - not able to load content from remote data source.')

	def query(self, g, query_str):
		"""Queries a data sources using a given graph.
		"""
		try:
			if self.access_method == Datasource.ACCESS_DOCUMENT: # the data source is an RDF document
				if self.access_mode == Datasource.MODE_LOCAL: # it's a local data source, hence we assume it has already been synced
					if self.sync_status(): 
						res = g.query(query_str)
					else:
						raise DatasourceNotSyncedError
				else: # Datasource.MODE_REMOTE
					tmp = Graph()
					self._load_from_file(tmp)
					res = tmp.query(query_str)
			else: # Datasource.ACCESS_SPARQL_ENDPOINT -> the data source is a SPARQL Endpoint, currently no disctinction between local and remote
				res = self._query_SPARQL_Endpoint(self.access_uri, query_str)
		except DatasourceAccessError, d:
			_logger.debug('Query failed - not able to access data source: %s' %type(d))
			return None
		return res

	def _load_from_file(self, g):
		try:
			_logger.debug('Trying to load %s into data source [%s]' %(self.access_uri, str(self.id)))
			if self.access_uri.endswith('.rdf'):
				g.parse(location = self.access_uri)
			elif self.access_uri.endswith('.ttl') or self.access_uri.endswith('.n3') :
				g.parse(location = self.access_uri, format="n3")
			elif self.access_uri.endswith('.nt'):
				g.parse(location = self.access_uri, format="nt")
			elif self.access_uri.endswith('.html'):
				g.parse(location = self.access_uri, format="rdfa")
			else:
				g.parse(location = self.access_uri)
		except Exception:
			raise DatasourceLoadError

	def _query_SPARQL_Endpoint(self, endpoint_URI, query_str):
		try:
			sparql = SPARQLWrapper(endpoint_URI)
			sparql.setQuery(query_str)
			sparql.setReturnFormat(JSON)
			results = sparql.query().convert()
			results = SPARQLQueryResult(results)
			return results
		except Exception, e:
			_logger.debug('SPARQL access failed - %s' %e)
			raise DatasourceAccessError
		#for result in results["results"]["bindings"]:
		#    print result["label"]["value"]

if __name__ == '__main__':
	_logger = logging.getLogger('ds')
	_logger.setLevel(logging.DEBUG)
	_handler = logging.StreamHandler()
	_handler.setFormatter(logging.Formatter('%(name)s %(levelname)s: %(message)s'))
	_logger.addHandler(_handler)

	q = """	SELECT * 
					WHERE { 
						?s ?p ?o .
					}
					LIMIT 3
	"""

	dslist = { 	'RDF/XML' : 'examples/statistics-ireland.rdf',
			#	'NTriple' : 'examples/business-data.gov.uk.nt',
			#	'Turtle'  : 'examples/dbpedia-ireland.ttl',
			#	'RDFa'    : 'examples/cygri-foaf.html'
			}
	
	for s in dslist.keys():
		print('='*50)
		print('Creating local data source: %s' %s)
		g = Graph()
		ds = Datasource('http://localhost:6969/api/datasource/', 'datasources/')
		ds.update(s, Datasource.ACCESS_DOCUMENT, dslist[s], Datasource.MODE_LOCAL)
		ds.sync(g)
		res = ds.query(g, q)
		print(res)
	
	g = Graph()
	ds = Datasource('http://localhost:6969/api/datasource/', 'datasources/')
#	ds.update('SPARQL test', Datasource.ACCESS_SPARQL_ENDPOINT, 'http://acm.rkbexplorer.com/sparql', Datasource.MODE_REMOTE)
	ds.update('SPARQL test', Datasource.ACCESS_SPARQL_ENDPOINT, 'http://dbpedia.org/sparql', Datasource.MODE_REMOTE)
	res = ds.query(g, q)
	print(res)