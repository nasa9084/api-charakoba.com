#!/usr/bin/env python
# -*- coding:utf-8 -*-

from hashlib import md5, sha256


def hash_password(password, email):
    stretch_idx = 30
    symbol_score = 4
    symbol_score -= 1 if re.match("[a-z]", password) else 0
    symbol_score -= 1 if re.match("[A-Z]", password) else 0
    symbol_score -= 1 if re.match("[0-9]", password) else 0
    symbol_score -= 1 if re.match("[!#$%&+*_.,/@^-]", password) else 0
    length_score = 25 - len(password) if len(password) < 25 else 0
    loop = stretch_idx * symbol_score * length_score
    salt = md5(email).hexdigest()
    digest = sha256(password + salt).hexdigest()
    for i in range(loop):
        digest = sha256(digest + salt).hexdigest()
    return digest
