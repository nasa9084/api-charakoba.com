#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json

def message(msg):
    return json.dumps({'message': msg})
