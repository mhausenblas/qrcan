#!/usr/bin/env python
# encoding: utf-8
"""
qrcan_store.py

Created by Michael Hausenblas on 2011-03-07.
"""
import logging
_logger = logging.getLogger('qrcan')

from rdflib import Graph
from rdflib import Namespace
from rdflib import URIRef
from rdflib import Literal
from rdflib import RDF
from rdflib import XSD
from SPARQLWrapper import SPARQLWrapper, JSON


class QrcanStore(object):
	MODE_INTERNAL = 'internal'
	MODE_EXTERNAL = 'external'
	
	def __init__(self):
		self.mode = QrcanStore.MODE_INTERNAL
		self.spaces = dict()
	
	def add_datasource_doc(self, space_id, doc_uri):
		g = Graph() # TODO: should use Store for it
		try:
			_logger.info('Trying to load %s' %doc_uri)
			g.parse(doc_uri)
		except PluginException:
			pass
		self.spaces[space_id] = g
		
	def query_datasource(self, space_id, query_str):
		g = self.spaces[space_id]
		res = g.query(query_str)
		
	def _remote_sync_SPARQL(self, query_str, endpoint_URI):
		sparql = SPARQLWrapper(endpoint_URI)
		sparql.setQuery(query_str)
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()

		for result in results["results"]["bindings"]:
		    print result["label"]["value"]

if __name__ == '__main__':
	qstore = QrcanStore()
	qstore._remote_sync_SPARQL("""
	    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	    SELECT ?label
	    WHERE { <http://dbpedia.org/resource/Asturias> rdfs:label ?label }
	""", "http://dbpedia.org/sparql")