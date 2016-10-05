#!/usr/bin/env python
# -*- coding:utf-8 -*-

output_dir = 'output'
dns_conf_filename = 'dns.zone'
rproxy_conf_filename = '{host}.proxy.conf'

token_prefix = 'chapi'
token_ttl = 24

mysql = {
    'host': 'localhost',
    'db': 'database_name',
    'user': 'user_name',
    'passwd': 'password',
    'charset': 'utf8'
}

redis = {
    'host': 'localhost',
    'port': 6389,
    'db': 0
}
