#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import request
import functools
from redis import Redis

import config
from lib.user import User


class Service(object):
    '''Whole Service Class'''
    @staticmethod
    def auth(func):
        '''Password-Base Authentication Decorator'''
        from lib.exceptions import AuthenticationError
        from lib.exceptions import UserNotActivatedError

        @functools.wraps(func)
        def inner(*a, **kw):
            id_ = request.params.get('id')
            password = request.params.get('password')
            if id_ is None or password is None:
                raise AuthenticationError
            user = User(id_)
            if not user.password_auth(password):
                raise AuthenticationError
            if not user.is_active:
                raise UserNotActivatedError
            return func(user=user, *a, **kw)
        return inner

    @staticmethod
    def token(func):
        '''Token-base Authentication Decorator'''
        from lib.exceptions import TokenError
        from lib.exceptions import UserNotActivatedError

        @functools.wraps(func)
        def inner(*a, **kw):
            token = request.params.get('token')
            if token is None:
                raise TokenError
            user = User(Service._get_user_id_from_token(token))
            if not user.is_active:
                raise UserNotActivatedError
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
                if not user.role <= role:
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
                params = {}
                for key in requirements:
                    assert type(key) == str
                    if key not in form:
                        raise ParameterRequirementsError
                    params[key] = form[key]
                return func(requirements=params, *a, **kw)
            return inner
        return outer

    @staticmethod
    def option_param(*options):
        '''Decorator Method Check the Request Parameter'''
        def outer(func):
            @functools.wraps(func)
            def inner(*a, **kw):
                form = reuqest.params
                params = {}
                for key in options:
                    assert type(key) == str
                    if key in form:
                        params[key] = form[key]
                return func(options=params, *a, **kw)
            return inner
        return outer


    @staticmethod
    def _get_user_id_from_token(token):
        '''Get User ID From Token'''
        from lib.exceptions import TokenError

        redis = Redis(**config.redis)
        id_ = redis.get(token)
        if id_ is None:
            raise TokenError
        return id_
