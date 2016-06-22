#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json

with open('config.json', 'r') as f:
    cfg = json.load(f)


def is_alive():
    res = requests.get(
        cfg['IN_API']['ENDPOINT']
    )
    if res.status_code == 200:
        return True
    else:
        return False


def add_user(username, publickey):
    payload = {
        'mode': 'add',
        'apikey': cfg['IN_API']['APIKEY'],
        'user': username,
        'publickey': publickey
    }
    res = requests.post(
        cfg['IN_API']['ENDPOINT'],
        data=payload
    )
    if res.status_code == 200 and res.text == 'Succeeded':
        return True
    else:
        return False
