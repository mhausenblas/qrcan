#!/usr/bin/env python
# encoding: utf-8
"""
qrcan_exceptions.py

Created by Michael Hausenblas on 2011-03-07.
"""

# HTTP interface exceptions

class HTTP404(Exception): pass

# data source excpetions
class DatasourceNotExists(Exception): pass

class DatasourceAccessError(Exception): pass

class DatasourceLoadError(DatasourceAccessError): pass

class DatasourceNotSyncedError(DatasourceAccessError): pass
