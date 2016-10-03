#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import HTTPError

import lib.message as msg


class CharakobaError(HTTPError):
    '''Base Exception Class of charakoba.com'''
    default_body = ''

    def __init__(
            self,
            status=None,
            body='',
            exception=None,
            traceback=None,
            **more_headers
    ):
        body = body or self.default_body
        super().__init__(status, body, exception, traceback, **more_headers)


class AuthenticationError(CharakobaError):
    default_status = 401
    default_body = {'message': msg.AUTH_ERROR}


class ParameterRequirementsError(CharakobaError):
    default_status = 400
    default_body = {'message': msg.PARAM_ERROR}


class PermissionError(CharakobaError):
    default_status = 403
    default_body = {'message': msg.PERMISSION_ERROR}


class RecordNotFoundError(CharakobaError):
    default_status = 404
    default_body = {'message': msg.RECORD_NOT_FOUND_ERROR}


class TokenError(CharakobaError):
    default_status = 401
    default_body = {'message': msg.TOKEN_ERROR}


class UserNotActivatedError(CharakobaError):
    default_status = 403
    default_body = {'message': msg.USER_NOT_FOUND_ERROR}


class UserNotFoundError(HTTPError):
    default_status = 404
    default_body = {'message': msg.USER_NOT_FOUND_ERROR}
