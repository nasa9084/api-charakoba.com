#!/usr/bin/env python
# -*- coding:utf-8 -*-

from nose.tools import eq_, ok_
import pymysql
import subprocess as shell
from unittest import TestCase

from json2mysql import build_queries, load_schema
from user import User, Role

class UserTestCase(TestCase):
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

    def test_user_update(self):
        old_username = 'Taro'
        old_password = 'password'
        old_role = 'user'
        user = User.create(
            old_username,
            old_password,
            old_role
        )
        ok_(user.password_auth(old_password))
        eq_(user.role, Role.user)
        new_username = 'Jiro'
        new_password = 'new_password'
        new_role = 'admin'
        user.update(
            new_username,
            new_password,
            new_role
        )
        ok_(not user.password_auth(old_password))
        ok_(user.password_auth(new_password))
        eq_(user.role, Role.admin)
        user.update(
            role=old_role
        )
        ok_(user.password_auth(new_password))
        eq_(user.role, Role.user)
