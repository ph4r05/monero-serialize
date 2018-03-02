#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Extremely minimal streaming codec for a subset of protobuf.  Supports uint32,
bytes, string, embedded message and repeated fields.

For de-sererializing (loading) protobuf types, object with `AsyncReader`
interface is required:

>>> class AsyncReader:
>>>     async def areadinto(self, buffer):
>>>         """
>>>         Reads `len(buffer)` bytes into `buffer`, or raises `EOFError`.
>>>         """

For serializing (dumping) protobuf types, object with `AsyncWriter` interface is
required:

>>> class AsyncWriter:
>>>     async def awrite(self, buffer):
>>>         """
>>>         Writes all bytes from `buffer`, or raises `EOFError`.
>>>         """
'''

const = lambda x: x


_UVARINT_BUFFER = bytearray(1)


async def load_uvarint(reader):
    buffer = _UVARINT_BUFFER
    result = 0
    shift = 0
    byte = 0x80
    while byte & 0x80:
        await reader.areadinto(buffer)
        byte = buffer[0]
        result += (byte & 0x7F) << shift
        shift += 7
    return result


async def dump_uvarint(writer, n):
    buffer = _UVARINT_BUFFER
    shifted = True
    while shifted:
        shifted = n >> 7
        buffer[0] = (n & 0x7F) | (0x80 if shifted else 0x00)
        await writer.awrite(buffer)
        n = shifted


class LimitedReader:

    def __init__(self, reader, limit):
        self.reader = reader
        self.limit = limit

    async def areadinto(self, buf):
        if self.limit < len(buf):
            raise EOFError
        else:
            nread = await self.reader.areadinto(buf)
            self.limit -= nread
            return nread


class CountingWriter:

    def __init__(self):
        self.size = 0

    async def awrite(self, buf):
        nwritten = len(buf)
        self.size += nwritten
        return nwritten


class AHashWriter:

    def __init__(self, hasher, sub_writer=None):
        self.hasher = hasher
        self.sub_writer = sub_writer

    async def awrite(self, buf):
        self.hasher.update(buf)
        if self.sub_writer:
            await self.sub_writer.awrite(buf)
        return len(buf)

    def get_digest(self, *args) -> bytes:
        return self.hasher.digest(*args)

