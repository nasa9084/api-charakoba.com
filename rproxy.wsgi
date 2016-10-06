#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle

from lib.common import message
from lib.records import ReverseProxyRecord
from lib.service import Service

app = application = Bottle()


@app.get('/')
def index():
    return message('Hello')


@app.get('/json')
def list_records():
    return ReverseProxyRecord.json()


@app.post('/')
@Service.token
@Service.role('admin')
@Service.require_param('host', 'upstream')
def add_record(user, params):
    record = ReverseProxyRecord.create(**params)
    return str(record)


@app.put('/<id_:int>')
@Service.token
@Service.role('admin')
@Service.option_param('host', 'upstream')
def update_record(params, user, id_):
    record = ReverseProxyRecord(id_)
    record.update(**params)
    return str(record)


@app.delete('/<id_:int>')
@Service.token
@Service.role('admin')
def delete_record(user, id_):
    record = ReverseProxyRecord(id_)
    record.delete()
    return message('Success')


@app.error(400)
@app.error(401)
@app.error(403)
@app.error(404)
def error_route(err):
    return message(err.body)

if __name__ == '__main__':
    app.run(reloader=True)
