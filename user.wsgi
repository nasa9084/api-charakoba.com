#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle
import json

from common import Service, Users, User, params, AuthenticationError

app = application = Bottle()
get = app.get
post = app.post
put = app.put
delete = app.delete
error = app.error

@get('/')
def ping():
    return {'status': 'LIVE'}


@post('/')
@params(require=['username', 'password', 'email', 'role'])
def add_user(params):
    params['passwd'] = params['password']
    del params['password']
    return {'ID': Users().add(**params).uid}


@get('/json')
@Service.auth
def list_user(user):
    return json.dumps([str(u) for u in Users().list()])


@put('/password')
@Service.auth
@params(require=['new_password'])
def update_user_passwd(user, params):
    user.update_passwd(params['new_password'])


@delete('/<id_:int>')
@Service.auth
def delete_user(user, id_):
    Users().delete(uid)


@error(400)
@error(401)
@error(404)
@error(405)
def error404(err):
    return json.dumps({'message': err.body})


if __name__ == '__main__':
    app.run(reloader=True, debug=True)
