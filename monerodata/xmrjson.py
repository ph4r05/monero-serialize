#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Monero JSON codec.

Note: This is not optimized for memory usage.
Used for debugging.
'''

from .protobuf import const, load_uvarint, dump_uvarint, LimitedReader, CountingWriter
from . import xmrserialize as x


class Archive(x.Archive):

    def __init__(self, iobj, writing=True, **kwargs):
        super().__init__(iobj, writing, **kwargs)

