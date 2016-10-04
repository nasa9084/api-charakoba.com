#!/usr/bin/env python
# -*- coding:utf-8 -*-

from enum import Enum
import json
import pymysql as DB
from pymysql.cursors import DictCursor as DC
from redis import Redis

import config


class Password(object):
    '''Enhashed Password Class
    This class provide comparable enhashed password'''
    from hashlib import sha512

    def __init__(self, password, alg=sha512):
        self.alg = alg
        self.password = self.alg(self._to_bytes(password)).hexdigest()

    def __eq__(self, other):
        if other is None or not type(other) == type(self):
            return False
        return self.password == other.password

    def __repr__(self):
        return self.password

    def _to_bytes(self, str_or_bytes):
        if type(str_or_bytes) == str:
            return str_or_bytes.encode('utf-8')
        else:
            return str_or_bytes


class Role(Enum):
    '''Service User Role Class
    Value of Higher Role is Lower'''
    admin = 1
    user = 2

    def __lt__(self, other):
        return self.value < self.other

    def __le__(self, other):
        return self.value <= self.other


class User(object):
    '''Service User Class'''
    @classmethod
    def create(cls, username, password, role=Role.user):
        '''this method create New User'''
        with DB.connect(**config.mysql) as cursor:
            cursor.execute(
                'INSERT INTO users '
                '(username, password, role) '
                'VALUES (%s, %s, %s);',
                (username, str(Password(password)), str(Role(role)))
            )
        return cls(cursor.lastrowid)

    def __init__(self, id_):
        from lib.exceptions import UserNotFoundError

        self.id_ = id_
        with DB.connect(cursorclass=DC, **config.mysql) as cursor:
            cursor.execute(
                'SELECT username, password, role, is_active '
                'FROM users '
                'WHERE id=%s;',
                (self.id_,)
            )
            row = cursor.fetchone()
        if not row:
            raise UserNotFoundError
        self.username = row['username']
        self.password = Password(row['password'])
        self.role = Role(row['role'])
        self.is_active = bool(row['is_active'])

    def __repr__(self):
        return self.__class__.__name__ + '({})'.format(self.id_)

    def password_auth(self, password):
        '''Return True if given password is valid'''
        return self.password == Password(password)

    def activate(self):
        '''Activate User'''
        with DB.connect(**config.mysql) as cursor:
            cursor.execute(
                'UPDATE users '
                'SET is_activate=1 '
                'WHERE id=%s;',
                (self.id_,)
            )

    def update(self, username=None, password=None, role=None):
        '''Update User Info'''
        if username is not None:
            self.username = username
        if password is not None:
            self.password = Password(password)
        if role is not None:
            self.role = Role(role)
        with DB.connect(**config.mysql) as cursor:
            cursor.execute(
                'UPDATE users '
                'SET username=%s, password=%s, role=%s '
                'WHERE id=%s;',
                (self.username, self.password, self.role, self.id_)
            )

    def get_token(self):
        from uuid import uuid4
        redis = Redis(**config.redis)
        if redis.get(self.token):
            return self.token
        new_token = config.token_prefix + '-' + str(uuid4())
        redis.setex(new_token, self.id_, config.token_ttl * 60 * 60)
        self.token = new_token
        return self.token

    def delete(self):
        '''Delete User'''
        with DB.connect(**config.mysql) as cursor:
            cursor.execute(
                'DELETE FROM users '
                'WHERE id=%s;',
                (self.id_,)
            )
        self.__dict__ = {}
