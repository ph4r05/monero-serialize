#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Monero Boost codec, portable binary archive
'''

import base64
import collections
import json

from . import xmrserialize as x


_UVARINT_BUFFER = bytearray(1)


async def load_uvarint(reader):
    """
    Monero portable_binary_archive boost integer serialization
    :param reader:
    :return:
    """
    buffer = _UVARINT_BUFFER
    await reader.areadinto(buffer)
    size = buffer[0]
    if size == 0:
        return 0

    negative = size < 0
    size = -size if negative else size
    result = 0
    shift = 0

    # TODO: endianity, rev bytes if needed
    for _ in range(size):
        await reader.areadinto(buffer)
        result += buffer[0] << shift
        shift += 8
    return result if not negative else -result


async def dump_uvarint(writer, n):
    """
    Monero portable_binary_archive boost integer serialization
    :param writer:
    :param n:
    :return:
    """
    buffer = _UVARINT_BUFFER
    if n == 0:
        buffer[0] = 0
        return await writer.awrite(buffer)

    negative = n < 0
    ll = -n if negative else n

    size = 0
    while ll != 0:
        ll >>= 8
        size += 1

    buffer[0] = size
    await writer.awrite(buffer)

    ll = -n if negative else n

    # TODO: endianity, rev bytes if needed
    for _ in range(size):
        buffer[0] = n & 0xff
        await writer.awrite(buffer)
        ll >>= 8


class Archive(x.Archive):

    def __init__(self, iobj, writing=True, **kwargs):
        super().__init__(iobj, writing, **kwargs)


