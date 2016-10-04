#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import pymysql as DB
from pymysql.cursors import DictCursor as DC

import config


class BaseRecord(object):
    '''Super Class of Records'''
    tablename = None
    columns = []

    @classmethod
    def create(cls, **column_values):
        '''Create new Record'''
        bind_values = []
        for column_name in cls.columns:
            if column_name not in column_values:
                raise KeyError
            bind_values.append(column_values[column_name])
        with DB.connect(**config.mysql) as cursor:
            cursor.execute(
                'INSERT INTO {tablename} '
                '({columns}) '
                'VALUES ({placeholders});'.format(
                    tablename=cls.tablename,
                    columns=', '.join(cls.columns),
                    placeholders=', '.join(['%s' for _ in cls.columns]),
                ),
                bind_values
            )
        return cls(cursor.lastrowid)

    def __init__(self, id_):
        from lib.exceptions import RecordNotFoundError

        self.id_ = id_
        with DB.connect(cursorclass=DC, **config.mysql) as cursor:
            cursor.execute(
                'SELECT {columns} '
                'FROM {tablename} '
                'WHERE id=%s;'.format(
                    columns=', '.join(self.columns)
                ),
                (self.id_, )
            )
            row = cursor.fetchone()
        if not row:
            raise RecordNotFoundError
        for key, value in row.items():
            setattr(self, key, value)

    def __repr__(self):
        return self.__class__.__name__ + '({id_})'.formart(id_=self.id_)

    def __str__(self):
        return json.dumps(self.__dict__)

    def update(self, *kw):
        '''Update Record'''
        # set new value to member if new value in kw
        for column_name in self.columns:
            if column_name in kw:
                self[column_name] = kw[column_name]
        with DB.connect(**config.mysql) as cursor:
            cursor.execute(
                'UPDATE {tablename} '
                'SET {update_columns} '
                'WHERE id=%s;'.format(
                    tablename=self.tablename,
                    update_columns=', '.join([c + '=%' for c in self.columns])
                ),
                [self.__dict__[c] for c in self.columns] + [self.id_]
            )

    def delete(self):
        '''Delete Record'''
        with DB.connect(**config.mysql) as cursor:
            cursor.execute(
                'DELETE FROM {tablename} '
                'WHERE id=%s;'.format(tablename=self.tablename),
                (self.id_, )
            )
        self.__dict__ = {}
