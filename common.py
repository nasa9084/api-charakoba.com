#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Library
from abc import abstractmethod, ABCMeta
from bottle import HTTPError, request
import functools
from hashlib import md5 as encode, sha512 as encrypt
import json
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
        super().__init__(400, msg)


class RecordNotFoundError(HTTPError):
    def __init__(self, rid):
        msg = messages.RECORD_NOT_FOUND + ': ' + str(rid)
        super().__init__(404, msg)


class UserNotActivatedError(HTTPError):
    def __init__(self):
        super().__init__(401, messages.USER_NOT_ACTIVATED)


class UserNotFoundError(HTTPError):
    def __init__(self, uid):
        msg = messages.USER_NOT_FOUND + ': ' + str(uid)
        super().__init__(404, msg)


class Service(object):
    '''Service Class'''
    def __init__(self):
        pass


class Users(object):
    '''Users Class'''
    def list(self):
        '''
        :returns: User Info Dict
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
        :returns: Created User object
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
        :param int uid: User ID you want to delete.
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
        :param int uid: User ID
        :raises UserNotFoundError: Not found user who has given user id
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

    def update_passwd(self, new_passwd):
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'UPDATE users '
                'SET password=%s '
                'WHERE id=%s;',
                (hash_passwd(new_passwd), self.uid)
            )

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


class BaseRecords(object, metaclass=ABCMeta):
    def __init__(self):
        self.table

    def json(self):
        '''List all Records and return json'''
        with DB.connect(cursorclass=DC, **config.RDB_INFO) as cursor:
            cursor.execute(
                'SELECT * FROM {};'.format(self.table)
            )
            result = cursor.fetchall()
        return json.dumps(result)

    def delete(self, id_):
        '''
        :param int id_: Record ID you want to delete
        '''
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'DELETE FROM {} '
                'WHERE id=%s;'.format(self.table),
                (id_)
            )

    @abstractmethod
    def add(self):
        '''
        :returns: 追加されたレコードオブジェクト
        :rtype: Record
        '''
        raise NotImplementedError


class BaseRecord(object, metaclass=ABCMeta):
    def __init__(self, id_):
        self.id_ = id_

    @abstractmethod
    def __str__(self):
        raise NotImplementedError

    @abstractmethod
    def update(self):
        raise NotImplementedError


class DNSRecords(BaseRecords):
    '''DNS Records class extends Base Records'''
    def __init__(self):
        self.table = 'dns'

    def add(self, type_, host, domain, ipv4_addr):
        '''
        :param str type_: DNS Record Type
        :param str host: Host name
        :param str domain: domain name
        :param str ipv4_addr: IPv4 address
        :return: DNSRecord Object that created
        :rtype: DNSRecord
        '''
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'INSERT INTO dns '
                '(type, host, domain, ipv4_addr) '
                'VALUES (%s, %s, %s, %s);',
                (type_, host, domain, ipv4_addr)
            )
        return DNSRecord(cursor.lastrowid)


class DNSRecord(BaseRecord):
    '''DNS Record Class extends BaseRecord'''
    def __init__(self, id_):
        with DB.connect(cursorclass=DC, **config.RDB_INFO) as cursor:
            cursor.execute(
                'SELECT type, host, domain, ipv4_addr '
                'FROM dns '
                'WHERE id=%s;',
                (id_, )
            )
            result = cursor.fetchone()
        if not result:
            raise RecordNotFoundError(id_)
        self.type_ = result['type']
        self.host = result['host']
        self.domain = result['domain']
        self.ipv4_addr = result['ipv4_addr']
        super().__init__(id_)

    def __str__(self):
        return '[DNS {} Record ID:{}] {}.{} -> {}'.format(
            self.type_, self.id_, self.host, self.domain, self.ipv4_addr
        )

    def update(self, type_=None, host=None, domain=None, ipv4_addr=None):
        '''
        :param type_: Record type e.g. A, MX, ...
        :type type_: str or None
        :param host: hostname that resolve from
        :type host: str or None
        :param domain: domain that resolve from
        :type domain: str or None
        :param ipv4_addr: ipv4 address that resolve to
        :type ipv4_addr: str or None
        '''
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'UPDATE dns '
                'SET type=%s, host=%s, domain=%s, ipv4_addr=%s '
                'WHERE id=%s;',
                (
                    type_ if type_ else self.type_,
                    host if host else self.host,
                    domain if domain else self.domain,
                    ipv4_addr if ipv4_addr else self.ipv4_addr,
                    self.id_
                )
            )
        return self


def params(require=[], option=[]):
    '''
    :decorator: Get form HTTP form parameters.
    :arg: The parameters will give with argument name: params.
    '''
    def _(func):
        @functools.wraps(func)
        def _(*ar, **kw):
            args = {}
            form_data = request.params
            for key in require:
                if key not in form_data:
                    raise ParameterRequirementsError(key)
                args[key] = form_data[key]
            for key in option:
                args[key] = form_data.get(key)
            return func(params=args, *ar, **kw)
        return _
    return _


def hash_passwd(passwd):
    '''
    :todo: choose a suitable salt
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
