#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Monero JSON codec.

Note: This is not optimized for memory usage.
Used for debugging.
'''

import base64
import collections
import json

from . import xmrserialize as x


class Archive(x.Archive):

    def __init__(self, iobj, writing=True, **kwargs):
        super().__init__(iobj, writing, **kwargs)


class AutoJSONEncoder(json.JSONEncoder):
    """
    JSON encoder trying to_json() first
    """
    def default(self, obj):
        try:
            return obj.to_json()
        except AttributeError:
            return self.default_classic(obj)

    def default_classic(self, o):
        if isinstance(o, set):
            return list(o)
        elif isinstance(o, bytes):
            return str(o, 'utf8')
        else:
            return super(AutoJSONEncoder, self).default(o)


def json_dumps(obj, **kwargs):
    """
    Uses auto encoder to serialize the object
    :param obj:
    :param kwargs:
    :return:
    """
    return json.dumps(obj, cls=AutoJSONEncoder, **kwargs)

