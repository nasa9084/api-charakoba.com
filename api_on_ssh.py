#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import requests

with open('config.json', 'r') as f:
    cfg = json.load(f)['IN_API']


def is_alive():
    res = requests.get(
        cfg['ENDPOINT']
    )
    if res.status_code == 200:
        return True
    else:
        return False


def add_user(username, publickey):
    payload = {
        'mode': 'add',
        'apikey': cfg['APIKEY'],
        'user': username,
        'publickey': publickey
    }
    res = requests.post(
        cfg['ENDPOINT'],
        data=payload
    )
    if res.status_code == 200 and res.text == 'Succeeded':
        return True
    else:
        return False


def delete_user(username):
    payload = {
        'mode': 'del',
        'apikey': cfg['APIKEY'],
        'user': username
    }
    res = requests.post(
        cfg['ENDPOINT'],
        data=payload
    )
    if res.status_code == 200 and res.text == 'Succeeded':
        return True
    else:
        return False


def modify_publickey(username, publickey):
    payload = {
        'mode': 'mod',
        'apikey': cfg['APIKEY'],
        'user': username,
        'publickey': publickey
    }
    res = requests.post(
        cfg['ENDPOINT'],
        data=payload
    )
    if res.status_code == 200 and res.text == 'Succeeded':
        return True
    else:
        return False
