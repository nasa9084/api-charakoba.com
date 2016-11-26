#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import request
import functools
from redis import Redis

import config
from lib.user import User, Role


class Service(object):
    '''Whole Service Class'''
    @staticmethod
    def auth(func):
        '''Password-Base Authentication Decorator'''
        from lib.exceptions import AuthenticationError

        @functools.wraps(func)
        def inner(*a, **kw):
            username = request.params.get('username') or kw.get('username')
            password = request.params.get('password')
            if username is None or password is None:
                raise AuthenticationError
            user = User(username)
            if not user.password_auth(password):
                raise AuthenticationError
            return func(user=user, *a, **kw)
        return inner

    @staticmethod
    def token(func):
        '''Token-base Authentication Decorator'''
        from lib.exceptions import TokenError

        @functools.wraps(func)
        def inner(*a, **kw):
            token = request.params.get('token')
            if token is None:
                raise TokenError
            user = User(Service._get_username_from_token(token))
            return func(user=user, *a, **kw)
        return inner

    @staticmethod
    def role(role):
        '''Decorator Method Checking Role
        Use after auth() decorator'''
        from lib.exceptions import AuthenticationError

        def outer(func):
            @functools.wraps(func)
            def inner(*a, **kw):
                user = kw.get('user')
                if user is None:
                    raise AuthenticationError
                if not user.role <= Role[role]:
                    raise AuthenticationError
                return func(*a, **kw)
            return inner
        return outer

    @staticmethod
    def require_param(*requirements):
        '''Decorator Method Check the Request Parameter'''
        from lib.exceptions import ParameterRequirementsError

        def outer(func):
            @functools.wraps(func)
            def inner(*a, **kw):
                form = request.params
                params = Parameters()
                for key in requirements:
                    assert type(key) == str
                    if key not in form:
                        raise ParameterRequirementsError
                    params[key] = form[key]
                if kw.get('params'):
                    params = params.update(kw['params'])
                return func(params=params, *a, **kw)
            return inner
        return outer

    @staticmethod
    def option_param(*options):
        '''Decorator Method Check the Request Parameter'''
        def outer(func):
            @functools.wraps(func)
            def inner(*a, **kw):
                form = request.params
                params = Parameters()
                for key in options:
                    assert type(key) == str
                    if key in form:
                        params[key] = form[key]
                if kw.get('params'):
                    params = params.update(kw['params'])
                return func(params=params, *a, **kw)
            return inner
        return outer


    @staticmethod
    def _get_username_from_token(token):
        '''Get Username From Token'''
        from lib.exceptions import TokenError

        redis = Redis(**config.redis)
        username = redis.get(token)
        if username is None:
            raise TokenError
        return username


class Parameters(dict):
    '''HTTP Parameters dict-like Object'''
    def __getattribute__(self, key):
        return self[key]

    def __setattribute__(self, key, value):
        self[key] = value
