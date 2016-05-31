#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle, HTTPResponse, request
import json

app = Bottle()
post = app.post


@post('/')
def echo():
    res = HTTPResponse()
    body = dict()
    form = request.forms
    for k,v in form.items():
        body[k] = v
    res.body = json.dumps(body)
    return res
