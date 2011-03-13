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


class QrcanStore(object):
	MODE_INTERNAL = 'internal'
	MODE_EXTERNAL = 'external'
	
	def __init__(self):
		self.mode = QrcanStore.MODE_INTERNAL
		self.spaces = dict()
		
	def query_datasource(self, space_id, query_str):
		g = self.spaces[space_id]
		res = g.query(query_str)


if __name__ == '__main__':
	qstore = QrcanStore()
	qstore._remote_sync_SPARQL("""
	    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	    SELECT ?label
	    WHERE { <http://dbpedia.org/resource/Asturias> rdfs:label ?label }
	""", "http://dbpedia.org/sparql")