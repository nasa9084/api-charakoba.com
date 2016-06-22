#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle

app = application = Bottle()
get = app.get

@get('/')
def ping():
    return {'message': 'pong'}
