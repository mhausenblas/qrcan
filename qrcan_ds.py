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
from rdflib.plugin import PluginException
from SPARQLWrapper import SPARQLWrapper, JSON

rdflib.plugin.register('sparql', rdflib.query.Processor, 'rdfextras.sparql.processor', 'Processor')
rdflib.plugin.register('sparql', rdflib.query.Result, 'rdfextras.sparql.query', 'SPARQLQueryResult')

from qrcan_exceptions import *

class Datasource:
	"""A data source
	
	Represents a data source in qrcan, including loading from/storing 
	to a file using VoID and other vocabularies to persist the state.
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
		self.updated = self._timestamp_now()
		self.access_method = Datasource.ACCESS_DOCUMENT
		self.access_uri = ''
		self.access_mode = Datasource.MODE_REMOTE
		self.last_sync = None
		self.num_triples = 0
		self.delta_triples = 0
		self.g.bind('void', Datasource.NAMESPACES['void'], True)
		self.g.bind('dcterms', Datasource.NAMESPACES['dcterms'], True)
		self.g.bind('qrcan', Datasource.NAMESPACES['qrcan'], True)

	def identify(self):
		"""Returns the ID of the data source as string.
		"""
		return str(self.id)

	def sync_status(self):
		"""Returns the synchronisation status of the data source.
		
		False if not yet synced, True otherwise.
		"""
		if self.last_sync:
			return True
		else:
			return False

	def is_local(self):
		if self.access_mode == Datasource.MODE_LOCAL: return True
		else: return False

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
								OPTIONAL { ?ds void:triples ?numTriples . } 
								OPTIONAL { ?ds qrcan:delta ?deltaTriples . } 
						}
		"""
		res = self.g.query(querystr, initNs=Datasource.NAMESPACES)
		for r in res.bindings:
			if r['ds']: self.id = r['ds']
			if r['title']: self.name = r['title']
			if r['modified']: self.updated = r['modified'].toPython()
			#_logger.debug('UPDATED: %s type: %s' %(self.updated, type(self.updated)))
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
					self.last_sync = r['lastSync'].toPython()
				else:
					self.last_sync = None
			except KeyError:
				pass
			try:
				if r['numTriples']:
					self.num_triples = int(r['numTriples'])
				else:
					self.num_triples = 0
			except KeyError:
				pass
			try:
				if r['deltaTriples']:
					self.delta_triples = int(r['deltaTriples'])
				else:
					self.delta_triples = 0
			except KeyError:
				pass

	def remove(self):
		"""Removes the data source.
		"""
		try:
			os.remove(self.file_name)
		except OSError:
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
		self.updated = self._timestamp_now()
		_logger.debug('UPDATED SAVE: %s type: %s' %(self.updated, type(self.updated)))
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
				self.g.set((URIRef(self.id), Datasource.NAMESPACES['void']['triples'], Literal(self.num_triples)))
				self.g.set((URIRef(self.id), Datasource.NAMESPACES['qrcan']['delta'], Literal(self.delta_triples)))
			else:
				self.g.remove((URIRef(self.id), Datasource.NAMESPACES['qrcan']['synced'], None))
				self.g.remove((URIRef(self.id), Datasource.NAMESPACES['void']['triples'], None))
				self.g.set((URIRef(self.id), Datasource.NAMESPACES['qrcan']['delta'], None))

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
					'updated' : self.updated.isoformat(),
					'access_method' : self.access_method,
					'access_uri' : self.access_uri,
					'access_mode' : self.access_mode
			}
			if self.access_mode == Datasource.MODE_LOCAL and self.sync_status():
				ds['last_sync'] =  self.last_sync.isoformat()
				ds['num_triples'] =  self.num_triples
				ds['delta_triples'] =  self.delta_triples
				
			
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
				self.last_sync = self._timestamp_now()
				old_num_triples = self.num_triples
				self.num_triples = len(g)
				self.delta_triples = self.num_triples - old_num_triples
				self.g.set((URIRef(self.id), Datasource.NAMESPACES['qrcan']['synced'], Literal(self.last_sync)))
				self.g.set((URIRef(self.id), Datasource.NAMESPACES['void']['triples'], Literal(self.num_triples)))
				self.g.set((URIRef(self.id), Datasource.NAMESPACES['qrcan']['delta'], Literal(self.delta_triples)))
			except DatasourceLoadError:
				_logger.debug('Sync failed - not able to load content from remote data source.')

	def query(self, g, query_str, encoding = 'str'):
		"""Queries a data sources using a given graph.
		"""
		res = None
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
		return self._format_results(res, encoding)

	def schema(self, g):
		"""Creates schema information about a data sources using a given graph.
		
		The schema info consists of a list of classes (from rdf:type, restricted to subjects with URIs) in descending order of occurrence. 
		"""
		res = self.query(g, """
		PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

		SELECT ?o WHERE { 
		?s rdf:type ?o .  
		FILTER (isURI(?s))
		} 
		""",
		encoding = 'raw')
		
		etypes = list()
		schemainfo = list()
		for r in res[1]:
			etypes.append(r['o']['value'])
		types = list(set(etypes)) # remove duplicates
		
		for t in types:
			atype =  dict()
			atype[etypes.count(t)] = t
			schemainfo.append(atype)
		
		return json.JSONEncoder().encode(sorted(schemainfo, reverse=True))

	def type_sample(self, g, turi):
		"""Creates schema information about an entity with a certain type using a given graph.
		"""
		res = self.query(g, 'SELECT ?s WHERE { ?s a <%s> . } LIMIT 1' % turi, encoding = 'raw')

		for r in res[1]:
			sample_uri = str(r['s']['value'])

		res = self.query(g, 'SELECT ?p ?o WHERE { <%s> ?p ?o . }' % sample_uri, encoding = 'raw')

		samples = list()
		prop_list = list()
		for r in res[1]:
			sample_prop = str(r['p']['value'])
			if not sample_prop in prop_list:
				prop_list.append(sample_prop)
				asample =  dict()
				asample[sample_prop] = r['o']['value']
				samples.append(asample)

		return json.JSONEncoder().encode(samples)


	def _format_results(self, results, encoding = 'str'):
		final_results = list()
		variables = list()
		bindings = list()
		if results:
			try:
				if results["results"]["bindings"]: # we have a SPARQL result from SPARQLWrapper
					variables = results["head"]["vars"]
					bindings = results["results"]["bindings"]
			except TypeError: # Graph-based query result from RDFlib
				for v in results.vars:
					variables.append(str(v))
				for res in results.bindings:
					field =  dict()
					for key in res.keys():
						r = res[key]
						entry = dict()
						if type(r) == rdflib.term.URIRef:
							entry['type'] = 'uri'
						if type(r) == rdflib.term.Literal:
							entry['type'] = 'literal'
						if type(r) == rdflib.term.BNode:
							entry['type'] = 'bnode'
						entry['value'] = str(r)
						field[str(key)] = entry
					bindings.append(field)
					#_logger.debug('type= %s key=%s entry=%s' %(type(r), key, entry))
			final_results.append(variables)
			final_results.append(bindings)
		else:
			final_results.append("none")
		
		if encoding == 'str':
			return json.JSONEncoder().encode(final_results)
		else:
			return final_results	

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
			return results
		except Exception, e:
			_logger.debug('SPARQL access failed - %s' %e)
			raise DatasourceAccessError
		
	def _timestamp_now(self):
		now = datetime.datetime.utcnow()
		return now.replace(microsecond = 0)

if __name__ == '__main__':
	_logger = logging.getLogger('ds')
	_logger.setLevel(logging.DEBUG)
	_handler = logging.StreamHandler()
	_handler.setFormatter(logging.Formatter('%(name)s %(levelname)s: %(message)s'))
	_logger.addHandler(_handler)

	q = """	SELECT ?who ?whom WHERE { ?who <http://xmlns.com/foaf/0.1/knows> ?whom . }
					LIMIT 2
	"""
	dslist = { 	'RDF/XML' : 'examples/statistics-ireland.rdf',
			#	'NTriple' : 'examples/business-data.gov.uk.nt',
			#	'Turtle'  : 'examples/dbpedia-ireland.ttl',
			#	'RDFa'    : 'examples/cygri-foaf.html'
			}
	
	#for s in dslist.keys():
	g = Graph()
	ds = Datasource('http://localhost:6969/api/datasource/', 'datasources/')

	ds.load('datasources/2a0df45e-4e59-11e0-a77e-002332baf36c.ttl')
	ds.sync(g)
	res = ds.schema(g)
	print(res)
	print('='*50)

	res = ds.type_sample(g, 'http://xmlns.com/foaf/0.1/Person')
	#for r in res:
	print(res)
	
	#ds = Datasource('http://localhost:6969/api/datasource/', 'datasources/')
	#ds.load('datasources/e2bd7c42-4dad-11e0-9d24-002332baf36c.ttl')
	#res = ds.query(g, q)
	#for r in res:
	#print(res)

	