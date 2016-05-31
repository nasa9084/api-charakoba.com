#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle, HTTPResponse, request
import json

app = Bottle()
post = app.post


@post('/')
def echo():
    res = HTTPResponse()
    form = request.forms
    if isinstance(form, dict):
        res.body = json.dumps(form)
    return res
