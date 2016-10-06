#!/usr/bin/env python
# -*- coding:utf-8 -*-

from lib.superclass import BaseRecord


class DNSRecord(BaseRecord):
    '''DNS Record Class'''
    tablename = 'dns'
    columns = ['type', 'host', 'ipv4_addr']


class ReverseProxyRecord(BaseRecord):
    '''Reverse Proxy Record Class'''
    tablename = 'rproxy'
    columns = ['host', 'upstream']
