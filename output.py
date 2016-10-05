#!/usr/bin/env python
# -*- coding:utf-8 -*-

from datetime import date
import pymysql as DB
from pymysql.cursors import DictCursor as DC
import os
import shutil

import config
from lib.exceptions import RecordNotFoundError


def main():
    _reset()
    output_dns()
    output_rproxy()


def output_dns():
    '''Output DNS Zone File'''
    def _build_record(row):
        return row['host'] + ' IN ' + row['type'] + ' ' + row['ipv4_addr']

    serial = date.today().strftime('%Y%m%d')
    with DB.connect(cursorclass=DC, **config.mysql) as cursor:
        cursor.execute('SELECT type, host, domain, ipv4_addr FROM dns;')
        rows = cursor.fetchall()
    if not rows:
        raise RecordNotFoundError
    records = [_build_record(row) for row in rows]
    template = _load_template('dns')
    output_path = os.path.join(config.output_dir, config.dns_conf_filename)
    with open(output_path, 'w') as f:
        f.write(
            template.format(
                serial=serial,
                records='\n'.join(records)
            ) + '\n'
        )


def output_rproxy():
    with DB.connect(cursorclass=DC, **config.mysql) as cursor:
        cursor.execute('SELECT host, upstream FROM rproxy;')
        rows = cursor.fetchall()
    if not rows:
        raise RecordNotFoundError
    template = _load_template('rproxy')
    for row in rows:
        output_path = os.path.join(
            config.output_dir,
            config.rproxy_conf_filename.format(host=row['host'])
        )
        with open(output_path, 'w') as f:
            f.write(
                template.format(
                    host=row['host'],
                    upstream=row['upstream']
                ) + '\n'
            )


def _reset():
    if os.path.exists(config.output_dir):
        shutil.rmtree(config.output_dir)
    os.mkdir(config.output_dir)


def _load_template(template_name):
    with open(os.path.join('templates', template_name + '.tmpl'), 'r') as f:
        return f.read()


if __name__ == '__main__':
    main()
