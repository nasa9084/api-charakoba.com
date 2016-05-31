#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle, HTTPResponse, request
import json

app = Bottle()
get = app.get


@get('/')
def ping():
    res = HTTPResponse()
    res.body = json.dumps({'message': 'pong'})
    return res
