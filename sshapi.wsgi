#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle, request, response
import json
import MySQLdb as DB
from MySQLdb.cursors import DictCursor as DC
import os

import api_on_ssh as InAPI
from common import apikey, param

conf = os.path.join(os.path.dirname(__file__), 'config.json')
with open(conf, 'r') as f:
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
@apikey
@param(require=['username', 'id', 'publickey'])
def add_user(param):
    if InAPI.add_user(param['username'], param['publickey']):
        with DB.connect(cursorclass=DC, **cfg['DB']) as cursor:
            try:
                cursor.execute(
                    '''INSERT INTO
                    ssh(id, user, publickey)
                    VALUES(%s, %s, %s);''',
                    (param['id'],
                     param['username'],
                     param['publickey'])
                )
            except:
                response.status = 400
                InAPI.delete_user(param['username'])
                return failed('Database Insert Error')
            else:
                return success()
    else:
        response.status = 400
        return failed('SSH Server API Error')


@delete('/')
@apikey
@param(require=['username', 'id'])
def delete_user(param):
    if InAPI.delete_user(param['username']):
        with DB.connect(cursorclass=DC, **cfg['DB']) as cursor:
            try:
                cursor.execute(
                    '''DELETE FROM ssh
                    WHERE id=%s;
                    ''',
                    (param['id'],)
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
@apikey
@param(require=['username', 'id', 'publickey'])
def modify_publickey(param):
    if InAPI.modify_publickey(param['username'], param['publickey']):
        with DB.connect(cursorclass=DC, **cfg['DB']) as cursor:
            try:
                cursor.execute(
                    '''UPDATE ssh
                    SET publickey=%s
                    WHERE id=%s;
                    ''',
                    (param['publickey'], param['id'])
                )
            except:
                response.status = 400
                return failed('Database Modify Error')
            else:
                return success()
    else:
        response.status = 400
        return failed('SSH Server API Error')


@get('/<id_:int>')
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
            response.status = 500
            return failed('Database Error')
        else:
            row = cursor.fetchone()
    if row:
        row['updated_at'] = row['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        return row
    else:
        response.status = 400
        return false('No Record')


@get('/init')
def initialize():
    if cfg['INIT']:
        with DB.connect(cursorclass=DC, **cfg['DB']) as cursor:
            try:
                cursor.execute(
                    '''CREATE TABLE ssh
                    (
                    id INT PRIMARY KEY,
                    user VARCHAR(128) NOT NULL,
                    publickey LONGTEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP
                    );
                    '''
                )
            except:
                response.status = 500
                return failed('Database Error')
            else:
                return success()
    else:
        response.status = 400
        return failed('Initialize is not Allowed')
