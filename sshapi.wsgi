#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle, request, response
import json
import MySQLdb as DB
from MySQLdb.cursors import DictCursor as DC

import api_on_ssh as InAPI
from common import param

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


@post('/')
@param(require=['username', 'id', 'publickey'])
def add_user(params):
    if InAPI.add_user(params['username'], params['publickey']):
        with DB.connect(cursorclass=DC, **cfg['DB']) as cursor:
            try:
                cursor.execute(
                    '''INSERT INTO
                    ssh(id, user, publickey)
                    VALUES(%s, %s, %s);''',
                    (params['id'],
                     params['username'],
                     params['publickey'])
                )
            except:
                response.status = 400
                InAPI.delete_user(params['username'])
                return failed('Database Insert Error')
            else:
                return success()
    else:
        response.status = 400
        return failed('SSH Server API Error')


@delete('/')
@param(require=['username', 'id'])
def delete_user(params):
    if InAPI.delete_user(params['username']):
        with DB.connect(cursorclass=DC, **cfg['DB']) as cursor:
            try:
                cursor.execute(
                    '''DELETE FROM ssh
                    WHERE id=%s;
                    ''',
                    (params['id'],)
                )
            except:
                response.status = 400
                return failed('Database Delete Error')
            else:
                return success()
    else:
        response.status = 400
        return failed('SSH Server API Error')


@put('/')
@param(require=['username', 'id', 'publickey'])
def modify_publickey(params):
    if InAPI.modify_publickey(params['username'], params['publickey']):
        with DB.connect(cursorclass=DC, **cfg['DB']) as cursor:
            try:
                cursor.execute(
                    '''UPDATE ssh
                    SET publickey=%s
                    WHERE id=%s;
                    ''',
                    (params['publickey'], params['id'])
                )
            except:
                response.status = 400
                return failed('Database Modify Error')
            else:
                return success()
    else:
        response.status = 400
        return failed('SSH Server API Error')


@get('/<id_:int>/')
def fetch(id_):
    with DB.connect(cursorclass=DC, **cfg['DB']) as cursor:
        try:
            cursor.execute(
                '''SELECT * FROM ssh
                WHERE id=%s;
                ''',
                (id_,)
            )
        except:
            response.status = 400
            return failed('Database Error')
        else:
            row = cursor.fetchone()
    if row:
        return row
    else:
        response.status = 400
        return false('No Record')
