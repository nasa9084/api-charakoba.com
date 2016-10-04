#!/usr/bin/env python
# -*- coding:utf-8 -*-

from nose.tools import eq_, ok_
import pymysql
import subprocess as shell
from unittest import TestCase

from json2mysql import build_queries, load_schema
from records import DNSRecord

class DNSTestCase(TestCase):
    def setUp(self):
        cmd = [
            "mysql",
            "-u", "root",
            "-e", "CREATE DATABASE charakoba_api;"
        ]
        shell.run(cmd)
        cmd = [
            "mysql",
            "-u", "root",
            "-D", "charakoba_api",
            "-e"
        ]
        qs = build_queries(load_schema('spec/mysql_schema.json'))
        for q in qs:
            print(q)
            shell.run(cmd + [q])

    def tearDown(self):
        cmd = [
            "mysql",
            "-u", "root",
            "-e", "DROP DATABASE charakoba_api;"
        ]
        shell.run(cmd)

    def test_dns_update(self):
        old_type = "A"
        old_host = "old"
        old_domain = "example.com"
        old_ipv4 = "192.168.0.1"
        record = DNSRecord.create(
            type=old_type,
            host=old_host,
            domain=old_domain,
            ipv4_addr=old_ipv4
        )
        eq_(record.type, old_type)
        eq_(record.host, old_host)
        eq_(record.domain, old_domain)
        eq_(record.ipv4_addr, old_ipv4)
        new_type = "AAAA"
        new_host = "new"
        new_domain = "new.example.com"
        new_ipv4 = "10.0.0.1"
        record.update(
            type=new_type,
            host=new_host,
            domain=new_domain,
            ipv4_addr=new_ipv4
        )
        eq_(record.type, new_type)
        eq_(record.host, new_host)
        eq_(record.domain, new_domain)
        eq_(record.ipv4_addr, new_ipv4)
