#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''json2mysql
convert json table schema to mysql query
'''

import json
import sys


def main():
    args = sys.argv
    if len(args) < 1:
        print('{} filename'.format(args[0]))
        quit()
    schema = load_schema(args[1])
    print(build_queries(schema))


def load_schema(filename):
    with open(filename, 'r') as f:
        schema = json.load(f)
    return schema


def build_queries(schema):
    tables = []
    for table in schema['tables']:
        tables.append(build_create_table(table))
    return tables


def build_create_table(table):
    return 'CREATE TABLE{exists} {tbl_name} ({defs}) {table_opts};'.format(
        exists=(' IF NOT EXISTS' if table.get('exists')==False else ''),
        tbl_name=table['name'],
        defs=create_definitions(table),
        table_opts=table_opts(table)
    )


def create_definitions(table):
    defs = []
    for col in table['columns']:
        defs.append(create_definition(col))
    for keyname in ['primary key', 'index', 'key', 'unique']:
        if table.get(keyname):
            key = table[keyname]
            state = ' ' + keyname.upper()
            state += index_type(key)
            state += '(' + ', '.join(key['columns']) + ')'
            defs.append(state)
    if table.get('foreign key'):
        fk = table['foreign key']
        state= ' FOREIGN KEY'
        if fk.get('columns'):
            state += ' (' + ', '.join(fk['columns']) + ')'
        elif fk.get('key'):
            state += ' (' + fk['key'] +')'
        state += reference_definition(fk)
        defs.append(state)
    definition = ', '.join(defs)
    return definition


def create_definition(col):
    definition = '{col_name} {col_def}'.format(
        col_name=col['name'],
        col_def=column_definition(col)
    )
    return definition


def column_definition(col):
    definition = data_type(col)

    if col.get('null'):
        definition += ' NULL'
    elif col.get('not null'):
        definition += ' NOT NULL'

    if col.get('default') is not None:
        definition += ' DEFAULT {}'.format(col['default'])

    if col.get('auto_increment') or col.get('auto increment'):
        definition += ' AUTO_INCREMENT'

    if col.get('unique'):
        definition += ' UNIQUE KEY'
    elif col.get('primary key') or col.get('primary'):
        definition += ' PRIMARY KEY'

    if col.get('comment'):
        definition += " COMMENT '{}'".format(col['comment'])

    if col.get('column_format'):
        definition += ' COLUMN_FORMAT {}'.format(col['column_format'])

    if col.get('storage'):
        definition += ' STORAGE {}'.format(col['storage'])

    definition += reference_definition(col)
    return definition


def reference_definition(col):
    definition = ''
    if col.get('reference'):
        definition = ' REFERENCES '
        ref = col['reference']
        definition += ref['table'] + '(' + ', '.join(ref['columns']) + ')'

        if ref.get('match'):
            definition += ' MATCH {}'.format(ref['match'])
        elif ref.get('match full'):
            definition += ' MATCH FULL'
        elif ref.get('match partial'):
            definition += ' MATCH PARTIAL'
        elif ref.get('match simple'):
            definition += ' MATCH SIMPLE'

        if ref.get('on delete'):
            definition += ' ON DELETE {}'.format(ref['on delete'])
        if ref.get('on update'):
            definition += ' ON UPDATE {}'.format(ref['on update'])
    return definition


def data_type(col):
    INTEGER = ['TINYINT', 'SMALLINT', 'MEDIUMINT', 'INT', 'INTEGER', 'BIGINT']
    FLOAT = ['REAL', 'DOUBLE', 'FLOAT']
    DECIMAL = ['DECIMAL', 'NUMERIC']
    DATETIME = ['DATE', 'DATETIME', 'TIMESTAMP', 'TIME', 'YEAR']
    CHARACTER = ['CHAR', 'VARCHAR']
    BINARY = ['BINARY', 'VARBINARY']
    BLOB = ['TINYBLOB', 'BLOB', 'MEDIUMBLOB', 'LONGBLOB']
    TEXT = ['TINYTEXT', 'TEXT', 'MEDIUMTEXT', 'LONGTEXT']

    type_ = col['type'].upper()
    if type_ in INTEGER + FLOAT + DECIMAL:
        if col.get('length'):
            type_ += '(' + str(col['length']) + ')'
        type_ += ' UNSIGNED' if col.get('unsigned') else ''
        type_ += ' ZEROFILL' if col.get('zerofill') else ''
    elif type_ in CHARACTER + BINARY:
        type_ += '(' + str(col.get('length', 128)) + ')'
        type_ += get_charset(col)
        type_ += get_collate(col)
    elif type_ in DATETIME:
        pass
    elif type_ in BLOB:
        pass
    elif type_ in TEXT:
        type_ += get_charset(col)
    elif type_ in ['ENUM', 'SET']:
        type_ += '(' + ', '.join(["'" + e + "'" for e in col['list']]) + ')'
        type_ += get_charset(col)
        type_ += get_collate(col)
    return type_


def get_charset(col):
    if col.get('charset'):
        return ' CHARACTER SET {}'.format(col['charset'])
    else:
        return ''


def get_collate(col):
    if col.get('collate'):
        return ' COLLATE {}'.format(col['collate'])
    return ''


def index_type(key):
    if key.get('using'):
        return ' USING {}'.format(key['using'])
    return ''


def table_opts(table):
    opts = []
    if table.get('engine'):
        opts.append('ENGINE {}'.format(table['engine']))
    if table.get('auto_increment'):
        if type(table['auto_increment']) == str:
            opts.append('AUTO_INCREMENT {}'.format(table['auto_increment']))
        elif type(table['auto_increment']) == list:
            for ai in table['auto_increment']:
                opts.append('AUTO_INCREMENT {}'.format(ai))
    if table.get('charset'):
        opts.append('CHARACTER SET {}'.format(table['charset']))
    if table.get('comment'):
        opts.append('COMMENT {}'.format(table['comment']))
    if table.get('insert_method') in ['NO', 'FIRST', 'LAST']:
        opts.append('INSERT_METHOD {}'.format(table['insert_method']))
    if table.get('max_rows'):
        opts.append('MAX_ROWS {}'.format(table['max_rows']))
    if table.get('min_rows'):
        opts.append('MIN_ROWS {}'.format(table['min_rows']))
    return ', '.join(opts)

if __name__ == '__main__':
    main()
