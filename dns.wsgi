#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle

from lib.common import message
from lib.records import DNSRecord
from lib.service import Service

app = application = Bottle()


@app.get('/')
def index():
    return message('Hello')


@app.post('/')
@Service.token
@Service.role('admin')
@Service.require_param('type', 'host', 'domain', 'ipv4_addr')
def add_record(params, user):
    record = DNSRecord.create(**params)
    return str(record)


@app.put('/<id_:int>')
@Service.token
@Service.role('admin')
@Service.option_param('type', 'host', 'domain', 'ipv4_addr')
def update_record(params, user, id_):
    record = DNSRecord(id_)
    record.update(**params)
    return str(record)


@app.delete('/<id_:int>')
@Service.token
@Service.role('admin')
def delete_record(user, id_):
    record = DNSRecord(id_)
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
