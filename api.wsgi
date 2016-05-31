#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import bottle
import sshapi
import ping

application = bottle.default_app()
application.mount('/ssh', sshapi.app)
application.mount('/ping', ping.app)
