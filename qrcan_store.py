#!/usr/bin/env python
# encoding: utf-8
"""
qrcan_store.py

Created by Michael Hausenblas on 2011-03-07.
"""
import logging
_logger = logging.getLogger('qrcan')

import os
import rdflib
from rdflib import plugin
from rdflib import Graph
from rdflib import Namespace
from rdflib import URIRef
from rdflib import Literal
from rdflib import RDF
from rdflib import XSD

from qrcan_ds import *


class QrcanStore(object):
	MODE_INTERNAL = 'internal'
	MODE_EXTERNAL = 'external'
	INTERNAL_CONTENT_DIR = 'dump/'
	
	def __init__(self):
		self.mode = QrcanStore.MODE_INTERNAL
		self.store = None
	
	def setup_store(self):
		if self.mode == QrcanStore.MODE_INTERNAL:
			if not os.path.exists(QrcanStore.INTERNAL_CONTENT_DIR):
				os.makedirs(QrcanStore.INTERNAL_CONTENT_DIR)
			self.store = dict()
		else: # QrcanStore.MODE_EXTERNAL not yet implemented
			pass
	
	def init_datasource(self, graph_uri):
		if self.mode == QrcanStore.MODE_INTERNAL:
			graph = Graph()
			self.store[graph_uri] = graph
			return graph
		else: # QrcanStore.MODE_EXTERNAL not yet implemented
			return None

	def store_datasource(self, graph, graph_uri):
		if self.mode == QrcanStore.MODE_INTERNAL:
			file_name = graph_uri.split('/')[-1]
			file_name = ''.join([QrcanStore.INTERNAL_CONTENT_DIR, file_name, '.nt'])
			dump_file = open(file_name, 'w')
			dump_file.write(graph.serialize(format='nt'))
			dump_file.close()
			_logger.debug('Dumped data source [%s] into %s' %(graph_uri, file_name))
		else: # QrcanStore.MODE_EXTERNAL not yet implemented
			return None

	def restore_datasource(self, graph, graph_uri):
		if self.mode == QrcanStore.MODE_INTERNAL:
			file_name = graph_uri.split('/')[-1]
			file_name = ''.join([QrcanStore.INTERNAL_CONTENT_DIR, file_name, '.nt'])
			g.parse(location = file_name, format="nt")
			_logger.debug('Restored data source [%s] from %s' %(graph_uri, file_name))
		else: # QrcanStore.MODE_EXTERNAL not yet implemented
			return None

	def is_datasource_available(self, graph_uri):
		if self.mode == QrcanStore.MODE_INTERNAL:
			if len(self.store[graph_uri]) == 0: return False
			else: return True
		else: # QrcanStore.MODE_EXTERNAL not yet implemented
			return None
			
if __name__ == '__main__':
	_logger = logging.getLogger('store')
	_logger.setLevel(logging.DEBUG)
	_handler = logging.StreamHandler()
	_handler.setFormatter(logging.Formatter('%(name)s %(levelname)s: %(message)s'))
	_logger.addHandler(_handler)

	q = """	SELECT ?s ?p
					WHERE { 
						?s ?p ?o .
					}
					LIMIT 3
	"""
	qstore = QrcanStore()
	qstore.setup_store()
	
	# create and store data source
	ds = Datasource('http://localhost:6969/api/datasource/', 'datasources/')
	ds.update('Local RDF/XML file stats', Datasource.ACCESS_DOCUMENT, 'examples/statistics-ireland.rdf', Datasource.MODE_LOCAL)
	
	g = qstore.init_datasource(ds.identify())
	print("data source content available: %s"  %qstore.is_datasource_available(ds.identify()))
	ds.sync(g)
	print("data source content available: %s" %qstore.is_datasource_available(ds.identify()))
	qstore.store_datasource(g, ds.identify())
	
	# restore data source	
	qstore = QrcanStore()
	qstore.setup_store()
	g = qstore.init_datasource(ds.identify())
	print("data source content available: %s"  %qstore.is_datasource_available(ds.identify()))
	qstore.restore_datasource(g, ds.identify())
	print("data source content available: %s" %qstore.is_datasource_available(ds.identify()))
	
	res = ds.query(g, q)
	for r in res:
		print(r)