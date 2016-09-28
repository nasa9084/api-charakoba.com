#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import Bottle
import json

from common import Service, DNSRecords, DNSRecord, params

app = application = Bottle()
get = app.get
post = app.post
put = app.put
delete = app.delete
error = app.error


@get('/')
def ping():
    return {'status': 'LIVE'}


@get('/record/json')
def get_record():
    return DNSRecords().json()


@get('/record/<id_:int>')
def get_record_from_id(id_):
    return [str(DNSRecord(id_))]


@post('/record')
@Service.auth
@params(require=['type', 'host', 'domain', 'ipv4_addr'])
def post_record(user, params):
    params['type_'] = params['type']
    del params['type']
    record = DNSRecords().add(**params)
    return {'id': str(record.id_)}


@put('/record/<id_:int>')
@Service.auth
@params(option=['type', 'host', 'domain', 'ipv4_addr'])
def put_record(user, id_, params):
    params['type_'] = params.get('type')
    if not params.get('type'):
        del params['type']
    DNSRecord(id_).update(**params)


@delete('/record/<id_:int>')
@Service.auth
def delete_record(user, id_):
    DNSRecords().delete(id_)


@error(400)
@error(401)
@error(404)
@error(405)
def error(err):
    return json.dumps({'message': err.body})


if __name__ == '__main__':
    app.run(reloader=True, debug=True)
