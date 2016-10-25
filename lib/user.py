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

    @classmethod
    def get_instance(cls, password):
        instance = cls('')
        instance.password = password
        return instance


class Role(Enum):
    '''Service User Role Class
    Value of Higher Role is Lower'''
    admin = 1
    user = 2

    def __lt__(self, other):
        return self.value < Role(other).value

    def __le__(self, other):
        return self.value <= Role(other).value


class User(object):
    '''Service User Class'''
    @classmethod
    def create(cls, username, password, role=Role.user.name):
        '''this method create New User'''
        with DB.connect(**config.mysql) as cursor:
            cursor.execute(
                'INSERT INTO users '
                '(username, password, role) '
                'VALUES (%s, %s, %s);',
                (username, str(Password(password)), role)
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
        self.password = Password.get_instance(row['password'])
        self.role = Role[row['role']]
        self.is_active = bool(row['is_active'])
        self.token = _get_id_token_dict().get(str(self.id_))

    def __repr__(self):
        return self.__class__.__name__ + '({})'.format(self.id_)

    def __str__(self):
        return json.dumps({
            "id": self.id_,
            "role": self.role.name,
            "is_active": self.is_active
        })

    def password_auth(self, password):
        '''Return True if given password is valid'''
        return self.password == Password(password)

    def activate(self):
        '''Activate User'''
        with DB.connect(**config.mysql) as cursor:
            cursor.execute(
                'UPDATE users '
                'SET is_active=1 '
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
            self.role = Role[role]
        with DB.connect(**config.mysql) as cursor:
            cursor.execute(
                'UPDATE users '
                'SET username=%s, password=%s, role=%s '
                'WHERE id=%s;',
                (self.username, str(self.password), self.role.value, self.id_)
            )

    def get_token(self):
        from uuid import uuid4
        from lib.exceptions import UserNotActivatedError, RedisConnectionError

        if not self.is_active:
            raise UserNotActivatedError
        redis = Redis(**config.redis)
        try:
            redis.ping()
        except:
            raise RedisConnectionError
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


def _get_id_token_dict():
    from lib.exceptions import RedisConnectionError

    redis = Redis(**config.redis)
    try:
        redis.ping()
    except:
        raise RedisConnectionError
    token_dict = {}
    for k in redis.keys('*'):
        k = k.decode()
        if k.startswith(config.token_prefix):
            token_dict[redis.get(k).decode()] = k
    return token_dict


def _token_id_dict():
    from lib.exceptions import RedisConnectionError

    redis = Redis(**config.redis)
    try:
        redis.ping()
    except:
        raise RedisConnectionError
    token_dict = {}
    for k in redis.keys('*'):
        k = k.decode()
        if k.startswith(config.token_prefix):
            token_dict[k] = redis.get(k).decode()
    return token_dict
