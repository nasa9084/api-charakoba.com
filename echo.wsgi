#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle, request

app = application = Bottle()
post = app.post

@post('/')
def echo():
    return request.forms
