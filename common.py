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
class AuthenticationError(HTTPError):
    def __init__(self):
        super().__init__(401, messages.AUTH_ERROR)


class ParameterRequirementsError(HTTPError):
    def __init__(self, key):
        msg = messages.REQUIRE.format(key)
        super().__init__(400, msg)


class RecordNotFoundError(HTTPError):
    def __init__(self, rid):
        msg = messages.RECORD_NOT_FOUND + ': ' + str(rid)
        super().__init__(404, msg)


class RoleCheckError(HTTPError):
    def __init__(self):
        msg = messages.ROLE_CHECK_ERROR
        super().__init__(405, msg)


class UserNotActivatedError(HTTPError):
    def __init__(self):
        super().__init__(401, messages.USER_NOT_ACTIVATED)


class UserNotFoundError(HTTPError):
    def __init__(self, uid):
        msg = messages.USER_NOT_FOUND + ': ' + str(uid)
        super().__init__(404, msg)


class Service(object):
    '''Service Class'''
    @staticmethod
    def auth(func):
        '''
        :decorator: user authentication with id and passwd
        '''
        @functools.wraps(func)
        def _(*ar, **kw):
            id_ = request.params.get('id')
            if id_ is None:
                raise ParameterRequirementsError('ID')
            passwd = request.params.get('password')
            if passwd is None:
                raise ParameterRequirementsError('password')
            user = User(id_)
            if user.password_auth(passwd):
                return func(user=User(id_), *ar, **kw)
            else:
                raise AuthenticationError
        return _

    @staticmethod
    def role(role):
        '''
        :decorator: user role checker
        '''
        def _(func):
            @funtools.wraps(func)
            def _(*ar, **kw):
                id_ = request.params.get('id')
                if id_ is None:
                    raise ParameterRequirementsError('ID')
                passwd = request.params.get('password')
                if passwd is None:
                    raise ParameterRequirementsError('passsword')
                user = User(id_)
                if user.role == role:
                    return func(*ar, **kw)
                else:
                    raise RoleCheckError
            return _
        return _


class Users(object):
    '''Users Class'''
    def list(self):
        '''
        :returns: generator of user
        :rtype: generator
        '''
        with DB.connect(cursorclass=DC, **config.RDB_INFO) as cursor:
            cursor.execute(
                'SELECT id '
                'FROM users '
                'WHERE is_delete=0;'
            )
            for user in cursor.fetchall():
                yield User(user['id'])

    def add(self, username, passwd, email, role):
        '''
        :returns: Created User object
        :rtype: User
        '''
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'INSERT INTO users '
                '(username, password, email, role, is_delete, is_active) '
                'VALUES (%s, %s, %s, %s, 0, 0);',
                (username, hash_passwd(passwd), email, role)
            )
        return User(cursor.lastrowid)

    def delete(self, uid):
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
                raise UserNotFoundError(uid)
        self.username = result['username']
        self.role = result['role']
        self.is_active = result['is_active']

    def __str__(self):
        return "[ID: {}] {} {}".format(self.uid, self.role, self.username)

    def activate(self):
        '''Activate User with mail verification.'''
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'UPDATE users '
                'SET is_active=1 '
                'WHERE id=%s;',
                (self.uid,)
            )

    def update_passwd(self, new_passwd):
        '''
        :param str new_passwd: New Password
        '''
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'UPDATE users '
                'SET password=%s '
                'WHERE id=%s;',
                (hash_passwd(new_passwd), self.uid)
            )

    def update_role(self, new_role):
        '''
        :param str new_role: New Role
        '''
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'UPDATE users '
                'SET role=%s '
                'WHERE id=%s;',
                (new_role, self.uid)
            )
        self.role = new_role

    def password_auth(self, passwd):
        '''
        :param str passwd: password you want to check
        :return: auth result
        :rtype: bool
        '''
        with DB.connect(cursorclass=DC, **config.RDB_INFO) as cursor:
            cursor.execute(
                'SELECT password '
                'FROM users '
                'WHERE id=%s;',
                (self.uid,)
            )
            result = cursor.fetchone()
        if hash_passwd(passwd) == result['password']:
            return True
        else:
            return False

    def create_token(self):
        '''
        :returns: token
        :rtype: str
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


class ReverseProxyRecords(BaseRecords):
    '''Reverse Proxy Records class extends BaseRecords'''
    def __init__(self):
        self.table = 'rproxy'

    def add(self, host, upstream):
        '''
        :param str host: hostname that resolved from
        :param str upstream: upstream hostname that resolve to
        '''
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'INSERT INTO {} '
                '(host, upstream) '
                'VALUES (%s, %s);'.format(self.table),
                (host, upstream)
            )
        return ReverseProxyRecord(cursor.lastrowid)


class ReverseProxyRecord(BaseRecord):
    '''Reverse Proxy Record Class extends BaseRecord'''
    def __init__(self, id_):
        with DB.connect(cursorclass=DC, **config.RDB_INFO) as cursor:
            cursor.execute(
            )
            result = cursor.fetchone()
        if not result:
            raise RecordNotFoundError(id_)
        self.host = result['host']
        self.upstream = result['upstream']
        super().__init__(id_)

    def __str__(self):
        return '[RPROXY Record ID:{}] {} -> {}'.format(
            self.id_, self.host, self.upstream
        )

    def update(self, host=None, upstream=None):
        '''
        :param host: hostname
        :type host: str or None
        :param upstream: upstream hostname
        :type upstream: str or None
        '''
        with DB.connect(**config.RDB_INFO) as cursor:
            cursor.execute(
                'UPDATE rproxy '
                'SET host=%s, upstream=%s '
                'WHERE id=%s;',
                (
                    host if host else self.host,
                    upstream if upstream else self.upstream
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
    salt = encode(passwd.encode()).hexdigest()
    digest = encrypt((passwd + salt).encode()).hexdigest()
    for i in range(loop):
        digest = encrypt((digest + salt).encode()).hexdigest()
    return digest
