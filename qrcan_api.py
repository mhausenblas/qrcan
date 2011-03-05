#!/usr/bin/env python
# encoding: utf-8
"""
qrcan_api.py

Created by Michael Hausenblas on 2011-03-04.
"""

import sys
import os
import rdflib
try:
    import json
except ImportError:
    import simplejson as json
from rdflib import Graph
from rdflib import Namespace

rdflib.plugin.register('sparql', rdflib.query.Processor, 'rdfextras.sparql.processor', 'Processor')
rdflib.plugin.register('sparql', rdflib.query.Result, 'rdfextras.sparql.query', 'SPARQLQueryResult')

class QrcanAPI:
	def __init__(self, out):
		self.datasources = Graph()
		self.out =  out
		self.apimap = {
				'/api/datasource/all' : 'list_all_datasets'
		}
		
	def dispatch_api_call(self, noun):
		try:
			m = getattr(self, self.apimap[str(noun)])
			m()
		except KeyError:
			print "Unknown noun %s" %noun

	def list_all_datasets(self):
		ns = {	'void' : Namespace('http://rdfs.org/ns/void#'),
				'dcterms' : Namespace('http://purl.org/dc/terms/')
		 }
		dslist = list()
		for f in os.listdir('datasources'):
			self.datasources.parse('datasources/' + f, format='n3')
		querystr = 'SELECT ?ds ?title WHERE { ?ds a void:Dataset ; dcterms:title ?title . }'
		for row in self.datasources.query(querystr, initNs=ns):
			ds, title = tuple(row)
			dslist.append({ 'id' : ds, 'title' : title})
		self.out.write(json.JSONEncoder().encode(dslist))