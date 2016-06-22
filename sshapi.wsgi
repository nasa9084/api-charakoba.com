#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle, request, response
import json

import api_on_ssh as InAPI

with open('config.json', 'r') as f:
    cfg = json.load(f)['SSH_API']

app = application = Bottle()
delete = app.delete
get = app.get
post = app.post
put = app.put


def failed(msg='Failed'):
    return {
        'status': False,
        'message': msg
    }


def success(msg='Succeeded'):
    return {
        'status': True,
        'message': msg
    }
