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


def unescape_json_str(st):
    """
    Unescape Monero json encoded string
    /monero/external/rapidjson/reader.h

    :param st:
    :return:
    """
    c = 0
    ln = len(st)
    escape_chmap = {
        b'b': b'\b',
        b'f': b'\f',
        b'n': b'\n',
        b'r': b'\r',
        b't': b'\t',
        b'\\': b'\\',
        b'"': b'\"',
        b'/': b'\/'
    }

    ret = []

    def at(i):
        return st[i:i+1]

    while c < ln:
        if at(c) == b'\\':
            if at(c+1) == b'u':
                ret.append(bytes([int(st[c+2:c+6], 16)]))
                # ret.append(st[c:c+6].decode('unicode_escape').encode('utf8'))
                c += 6

            else:
                ret.append(escape_chmap[at(c+1)])
                c += 2

        else:
            ret.append(at(c))
            c += 1

    df = (b''.join(ret))
    return df


def escape_string_json(st):
    """
    Escaping string for json
    /Users/dusanklinec/workspace/monero/external/rapidjson/writer.h
    :param st:
    :return:
    """
    ret = []
    c = 0
    ln = len(st)

    escape_chmap = {
        b'\b': b'b',
        b'\f': b'f',
        b'\n': b'n',
        b'\r': b'r',
        b'\t': b't',
        b'\\': b'\\',
        b'\"': b'"',
        b'\/': b'/'
    }

    while c < ln:
        ch = st[c:c+1]
        if ch in escape_chmap:
            ret.append(b'\\' + escape_chmap[ch])
        elif ord(ch) < 0x20:
            ret.append(b'\\u%04X' % ord(ch))
        else:
            ret.append(ch)
        c += 1
    return b''.join(ret)


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

