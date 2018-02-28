#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Monero JSON codec.

Note: This is not optimized for memory usage.
Used for debugging
'''

from .protobuf import const, load_uvarint, dump_uvarint, LimitedReader, CountingWriter

