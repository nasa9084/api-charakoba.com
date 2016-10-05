#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle
import json

from lib.common import message
from lib.service import Service
from lib.user import User

app = application = Bottle()


@app.get('/')
def index():
    return message('hello')


@app.post('/')
@Service.require_param('username', 'password')
def add_user(params):
    user = User.create(params.username, params.password)
    return str(user)


@app.put('/activate')
@Service.auth
def user_activate(user):
    user.activate()
    return json.dumps({'token': user.get_token()})


@app.post('/token')
@Service.auth
def get_token(user):
    return json.dumps({'token': user.get_token()})


@app.put('/')
@Service.token
@Service.option_param('username', 'password')
def update_user(user, params):
    user.update(**params)
    return str(user)


@app.delete('/')
@Service.token
def delete_user(user):
    user.delete()


@app.error(400)
@app.error(401)
@app.error(403)
@app.error(404)
def error_route(err):
    return message(err.body)

if __name__ == '__main__':
    app.run(reloader=True)
