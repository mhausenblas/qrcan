#!/usr/bin/env python
# encoding: utf-8
"""
qrcan_store.py

Created by Michael Hausenblas on 2011-03-07.
"""

from SPARQLWrapper import SPARQLWrapper, JSON


class QrcanStore(object):
		
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