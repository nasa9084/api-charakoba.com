#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle, HTTPResponse, request
import datetime
import MySQLdb
import requests

DB_INFO = {
    'db': 'charakoba_ssh',
    'user': 'ssh_register',
    'passwd': 'LFT2Dt2NyS'
}

MSG_ACCOUNT_EXISTS = 'account exists.'
MSG_REQUIRED = '{0} is required.'

res = HTTPResponse()
res.body = dict()

app = Bottle()
post = app.post
delete = app.delete
put = app.put

@post('/')
def add():
    endpoint = 'http://ssh.charakoba.com/api/'
    required = ['username', 'id', 'publickey', 'apikey']
    kv_dct = dict()
    kv_dct['mode'] = 'add'
    for key in required:
        if key in request.forms:
            kv_dct[key] = request.forms.get(key)
        else:
            res.status = 400
            res.body['message'] = MSG_REQUIRED.format(key)
            return res
    with MySQLdb.connect(**DB_INFO) as cursor:
        cursor.execute('SELECT * FROM ssh WHERE id=%s;', (kv_dct['id'],))
        record = cursor.fetchone()
        if record:
            res.status = 400
            res.body['message'] = MSG_ACCOUNT_EXISTS
            return res
        else:
            r = requests.post(
                    endpoint,
                    data=kv_dct
                )
            if chk_response(r):
                cursor.execute(
                    'INSERT INTO ssh(id, user, publickey) VALUES(%s, %s, %s);',
                    (kv_dct['id'], kv_dct['username'], kv_dct['publickey']))
    res.body['message'] = r.text
    return res


@delete('/')
def delete():
    endpoint = 'http://ssh.charakoba.com/api/'
    required = ['username', 'id', 'apikey']
    kv_dct = dict()
    for key in required:
        if key in request.forms:
            kv_dct[key] = request.forms.get(key)
        else:
            res.status = 400
            res.body['message'] = MSG_REQUIRED.format(key)
            return res
    kv_dct['mode'] = 'del'
    r = requests.post(
            endpoint,
            data=kv_dct
        )
    if chk_respoinse(r):
        with MySQLdb.connect(**DB_INFO) as cursor:
            cursor.execute('DELETE FROM ssh WHERE id=%s;',
                           (kv_dct['id'],))
    res.body['message'] = r.text
    return res


@put('/')
def mod():
    endpoint = 'http://ssh.charakoba.com/api/'
    required = ['username', 'id', 'publickey', 'apikey']
    kv_dct = dict()
    for key in required:
        if key in request.forms:
            kv_dct[key] = request.forms.get(key)
        else:
            res.status = 400
            res.body['message'] = MSG_REQUIRED.format(key)
            return res
    kv_dct['mode'] = 'mod'
    r = requests.post(
            endpoint,
            data=kv_dct
        )
    if chk_response(r):
        with MySQLdb.connect(**db_info) as cursor:
            cursor.execute('UPDATE ssh SET publickey=%s WHERE id=%s;',
                           (kv_dct['publickey'], kv_dct['id']))
    res.body['message'] = r.text
    return res


@post('/fetch')
def fetch():
    id_ = request.forms.get('id')
    if id_ is None:
        res.status = 400
        res.body['message'] = MSG_REQUIRED.format('id')
        return res
    with MySQLdb.connect(**DB_INFO) as cursor:
        cursor.execute('SELECT * FROM ssh WHERE id=%s;', (id_,))
        r = cursor.fetchone()
        if r:
            keys = ['id', 'user', 'publickey', 'updated_at']
            for k, v in zip(keys, r):
                if isinstance(v, datetime.datetime):
                    res.body[k] = v.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    res.body[k] = v
        else:
            res.body['message'] = 'No Record.'
    return res


@post('/isavail')
def isavail():
    endpoint = 'http://ssh.charakoba.com/api/check'
    required = ['username', 'apikey']
    kv_dct = dict()
    for key in required:
        if key in request.forms:
            kv_dct[key] = request.forms.get(key)
        else:
            res.status = 400
            res.body['message'] = MSG_REQUIRED.format(key)
            return res
    res.body['username'] = kv_dct['username']
    r = requests.post(
            endpoint,
            data=kv_dct,
        )
    if r.text != 'Present' and r.status_code == 200:
        res.body['isavailable'] = 'available'
    else:
        res.body['isavailable'] = 'unavailable'
    return res


def chk_response(res):
    return res.status_code == 200 and res.text in 'Succeeded'
