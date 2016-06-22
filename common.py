#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import request
from functools import wraps
from hashlib import md5, sha256
import json
import os

conf = os.path.join(os.path.dirname(__file__), 'config.json')
with open(conf, 'r') as f:
    cfg = json.load(f)


class APIKeyNotValidError(Exception):
    pass


class RequireNotSatisfiedError(Exception):
    pass


def apikey(func):
    @wraps(func)
    def _(*a, **ka):
        given = request.forms.get('apikey')
        if given == cfg['APIKEY']:
            func(*a, **ka)
        else:
            raise APIKeyNotValidError
    return _


def param(require=[], option=[]):
    def deco(func):
        @wraps(func)
        def _(*a, **ka):
            parameters = {}
            for key in require:
                if key in request.forms:
                    parameters[key] = request.forms.get(key)
                else:
                    raise RequireNotSatisfiedError(key)
            for key in option:
                if key in request.forms:
                    parameters[key] = request.forms.get(key)
                else:
                    pass
            func(param=parameters, *a, **ka)
        return _
    return deco


def hash_password(password, email):
    stretch_idx = 30
    symbol_score = 4
    symbol_score -= 1 if re.match("[a-z]", password) else 0
    symbol_score -= 1 if re.match("[A-Z]", password) else 0
    symbol_score -= 1 if re.match("[0-9]", password) else 0
    symbol_score -= 1 if re.match("[!#$%&+*_.,/@^-]", password) else 0
    length_score = 25 - len(password) if len(password) < 25 else 0
    loop = stretch_idx * symbol_score * length_score
    salt = md5(email).hexdigest()
    digest = sha256(password + salt).hexdigest()
    for i in range(loop):
        digest = sha256(digest + salt).hexdigest()
    return digest
