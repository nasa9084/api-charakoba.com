#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle

app = application = Bottle()

@app.any('/<path:path>')
def ping(path):
    return {'message': 'pong'}
