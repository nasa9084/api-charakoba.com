#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Library
from bottle import HTTPError, request
import functools
from hashlib import md5 as encode, sha512 as encrypt
import pymysql as DB
from pymysql.cursors import DictCursor as DC
import re
from redis import Redis
from uuid import uuid4

# Config
import config
import messages


# Exceptions
class ParameterRequirementsError(HTTPError):
    def __init__(self, key):
        msg = messages.REQUIRE.format(key)
        super.__init__(400, msg)


class UserNotActivatedError(HTTPError):
    def __init__(self):
        super.__init__(401, messages.USER_NOT_ACTIVATED)


class UserNotFoundError(HTTPError):
    def __init__(self, uid):
        msg = messages.USER_NOT_FOUND + ': ' + str(uid)
        super.__init__(404, msg)


class Service(object):
    '''Service Class'''
    def __init__(self):
        pass


class Users(object):
    '''Users Class'''
    def list_users(self):
        '''
        :returns: ユーザ情報の辞書
        :rtype: dict
        '''
        with DB.connect(cursorclass=DC, **config.RDB_INFO) as cursor:
            cursor.execute(
                'SELECT username, email, role '
                'FROM users;'
            )
            return cursor.fetchall()

    def add_user(self, username, passwd, email, role):
        '''
        :returns: 作成したユーザのオブジェクト
        :rtype: User
        '''
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'INSERT INTO users '
                '(username, password, email, role) '
                'VALUES (%s, %s, %s, %s);',
                (username, hash_passwd(passwd), email, role)
            )
            uid = cursor.lastrowid
        return User(uid)

    def delete_user(self, uid):
        '''
        :param int uid: 削除するユーザのID
        '''
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'UPDATE users '
                'SET is_delete=1 '
                'WHERE id=%s;',
                (uid,)
            )


class User(object):
    '''User Class'''
    def __init__(self, uid):
        '''
        :param int uid: ユーザID
        :raises UserNotFoundError: 該当するIDのユーザがいない場合
        '''
        self.uid = uid
        with DB.connect(cursorclass=DC, **config.RDB_INFO) as cursor:
            cursor.execute(
                'SELECT username, role, is_active '
                'FROM users '
                'WHERE id=%s;',
                (self.uid,)
            )
            result = cursor.fetchone()
            if not result:
                raise UserNotFoundError
        self.username = result['username']
        self.role = result['role']
        self.is_active = result['is_active']

    def activate(self):
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'UPDATE users '
                'SET is_active=1 '
                'WHERE id=%s;',
                (self.uid,)
            )

    def _is_active(self, func):
        @functools.wraps(func)
        def _(*ar, **kw):
            if not self.is_active:
                raise UserNotActivatedError
            return func(self, *ar, **kw)
        return _

    @_is_active
    def update_passwd(self, new_passwd):
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'UPDATE users '
                'SET password=%s '
                'WHERE id=%s;',
                (hash_passwd(new_passwd), self.uid)
            )

    @_is_active
    def create_token(self):
        '''
        :returns: token
        '''
        token = config.TOKEN_PREFIX + uuid4()
        redis = Redis(**config.REDIS_INFO)
        for key in redis.keys('*'):
            if redis.get(key) == self.uid:
                redis.delete(key)
        redis.setex(token, self.uid, config.APIKEY_TTL*60*60)
        return token


def params(require=[], option=[]):
    '''Get form parameters Decorator'''
    def _(func):
        @functools.wraps(func)
        def _(*ar, **kw):
            args = {}
            form_data = request.params
            for key in require:
                if not key in form_data:
                    raise ParameterRequirementsError(key)
                args[key] = form_data[key]
            for key in option:
                args[key] = form_data.get(key)
            return func(params=args, *ar, **kw)
        return _
    return _


def hash_passwd(passwd):
    '''
    :todo: 適切なソルトを選定する必要がある
    '''
    stretch_idx = 30
    # 文字種数スコア
    symbol_score = 4
    symbol_score -= 1 if re.match("[a-z]", passwd) else 0
    symbol_score -= 1 if re.match("[A-Z]", passwd) else 0
    symbol_score -= 1 if re.match("[0-9]", passwd) else 0
    symbol_score -= 1 if re.match("[!#$%&+*_.,/@^-]", passwd) else 0
    # パスワード長スコア
    length_score = 25 - len(passwd) if len(passwd) < 25 else 0
    # 文字種数、パスワード長が大きいほどループは不要
    loop = stretch_idx * symbol_score * length_score
    salt = encode(passwd).hexdigest()
    digest = encrypt(passwd + salt).hexdigest()
    for i in range(loop):
        digest = encrypt(digest + salt).hexdigest()
    return digest
