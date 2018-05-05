#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
XMR RPC serialization
WARNING: Not finished yet

{json, binary} <-> portable_storage <-> object

The portable storage is pretty much generic dict in python.
The original codec is not streaming in a sense directly translating input to object or vice versa.

Portable storage is an intermediate object.

Mainly related to:

/contrib/epee/include/serialization/keyvalue_serialization.h
/contrib/epee/include/serialization/keyvalue_serialization_overloads.h
/contrib/epee/include/storages/portable_storage.h
/contrib/epee/include/storages/portable_storage_base.h
/contrib/epee/include/storages/portable_storage_from_bin.h
/contrib/epee/include/storages/portable_storage_from_json.h
/contrib/epee/include/storages/portable_storage_to_bin.h
/contrib/epee/include/storages/portable_storage_to_json.h

WARNING: Not finished yet
'''

import binascii

from . import xmrserialize as x
from .xmrserialize import eref


_UINT_BUFFER = bytearray(1)


class PortableStorageConsts:
    SIGNATUREA = 0x01011101
    SIGNATUREB = 0x01020101
    FORMAT_VER = 1


class PortableRawSizeMark:
    MASK = 0x03
    BYTE = 0
    WORD = 1
    DWORD = 2
    INT64 = 3


class SerializeType:
    INT64 = 1
    INT32 = 2
    INT16 = 3
    INT8 = 4
    UINT64 = 5
    UINT32 = 6
    UINT16 = 7
    UINT8 = 8
    DUOBLE = 9
    STRING = 10
    BOOL = 11
    OBJECT = 12
    ARRAY = 13
    ARRAY_FLAG = 0x80


SerializeTypeSize = {
    SerializeType.INT64: 8,
    SerializeType.INT32: 2,
    SerializeType.INT16: 2,
    SerializeType.INT8: 1,
    SerializeType.UINT64: 8,
    SerializeType.UINT32: 2,
    SerializeType.UINT16: 2,
    SerializeType.UINT8: 1,
    SerializeType.BOOL: 1,
}


XmrTypeMap = {
    x.UVarintType: SerializeType.UINT64,
    x.Int64: SerializeType.INT64,
    x.Int32: SerializeType.INT32,
    x.Int16: SerializeType.INT16,
    x.Int8: SerializeType.INT8,
    x.UInt64: SerializeType.UINT64,
    x.UInt32: SerializeType.UINT32,
    x.UInt16: SerializeType.UINT16,
    x.UInt8: SerializeType.UINT8,
    x.BoolType: SerializeType.BOOL,
    x.UnicodeType: SerializeType.STRING,
    x.ContainerType: SerializeType.ARRAY,
    x.MessageType: SerializeType.OBJECT,
}


class IModel(object):
    def __init__(self, val, ser_type=None):
        self.val = val
        self.type = ser_type

    def __repr__(self):
        return '%r' % self.val

    def __eq__(self, other):
        if isinstance(other, IModel):
            return self.type == other.type and self.val == other.val
        else:
            return self.val == other

    def to_json(self):
        return self.val


class ArrayModel(IModel):
    def __str__(self):
        return 'Arr[%s; %s]' % (self.type, self.val)


class IntegerModel(IModel):
    def __str__(self):
        return 'Int[%s; %s]' % (self.type, self.val)


def int_mark_to_size(int_type):
    if int_type == PortableRawSizeMark.BYTE:
        return 1
    elif int_type == PortableRawSizeMark.WORD:
        return 2
    elif int_type == PortableRawSizeMark.DWORD:
        return 4
    elif int_type == PortableRawSizeMark.INT64:
        return 8
    else:
        raise ValueError('Unknown int type')


def type_to_size(obj_type):
    return SerializeTypeSize[obj_type]


def xmr_type_to_type(elem_type):
    if isinstance(elem_type, int):
        return elem_type
    elif elem_type in XmrTypeMap:
        return XmrTypeMap[elem_type]
    elif isinstance(elem_type, x.XmrType):
        return XmrTypeMap[elem_type.__class__]
    else:
        raise ValueError('Cannot convert Xmr type')


async def dump_varint_t(writer, type_or, pv):
    """
    Binary dump of the integer of given type

    :param writer:
    :param type_or:
    :param pv:
    :return:
    """
    width = int_mark_to_size(type_or)
    n = (pv << 2) | type_or

    buffer = _UINT_BUFFER
    for _ in range(width):
        buffer[0] = n & 0xff
        await writer.awrite(buffer)
        n >>= 8

    return width


async def dump_varint(writer, val):
    """
    Binary dump of the variable size integer

    :param writer:
    :param val:
    :return:
    """
    if val <= 63:
        return await dump_varint_t(writer, PortableRawSizeMark.BYTE, val)
    elif val <= 16383:
        return await dump_varint_t(writer, PortableRawSizeMark.WORD, val)
    elif val <= 1073741823:
        return await dump_varint_t(writer, PortableRawSizeMark.DWORD, val)
    else:
        if val > 4611686018427387903:
            raise ValueError('Int too big')
        return await dump_varint_t(writer, PortableRawSizeMark.INT64, val)


async def load_varint(reader):
    """
    Binary load of variable size integer serialized by dump_varint

    :param reader:
    :return:
    """
    buffer = _UINT_BUFFER

    await reader.areadinto(buffer)
    width = int_mark_to_size(buffer[0] & PortableRawSizeMark.MASK)
    result = buffer[0]

    shift = 8
    for _ in range(width-1):
        await reader.areadinto(buffer)
        result += buffer[0] << shift
        shift += 8
    return result >> 2


async def dump_string(writer, val):
    """
    Binary string dump

    :param writer:
    :param val:
    :return:
    """
    await dump_varint(writer, len(val))
    await writer.awrite(val)


async def load_string(reader):
    """
    Loads string from binary stream

    :param reader:
    :return:
    """
    ivalue = await load_varint(reader)
    fvalue = bytearray(ivalue)
    await reader.areadinto(fvalue)
    return bytes(fvalue)


async def dump_blob(writer, elem, elem_type, params=None):
    """
    Dumps blob to a binary stream

    :param writer:
    :param elem:
    :param elem_type:
    :param params:
    :return:
    """
    elem_is_blob = isinstance(elem, x.BlobType)
    data = getattr(elem, x.BlobType.DATA_ATTR) if elem_is_blob else elem
    await dump_varint(writer, len(elem))
    await writer.awrite(data)


async def load_blob(reader, elem_type, params=None, elem=None):
    """
    Loads blob from reader to the element. Returns the loaded blob.

    :param reader:
    :param elem_type:
    :param params:
    :param elem:
    :return:
    """
    ivalue = await load_varint(reader)
    fvalue = bytearray(ivalue)
    await reader.areadinto(fvalue)

    if elem is None:
        return fvalue  # array by default

    elif isinstance(elem, x.BlobType):
        setattr(elem, elem_type.DATA_ATTR, fvalue)
        return elem

    else:
        elem.extend(fvalue)

    return elem


#
# Archive
#


class Archive(x.Archive):
    def __init__(self, iobj, writing=True, modeled=True, **kwargs):
        super().__init__(iobj, writing, **kwargs)
        self.modeled = modeled

    async def root(self):
        """
        Root level init
        :return:
        """
        if self.writing:
            await x.dump_uint(self.iobj, PortableStorageConsts.SIGNATUREA, 4)
            await x.dump_uint(self.iobj, PortableStorageConsts.SIGNATUREB, 4)
            await x.dump_uint(self.iobj, PortableStorageConsts.FORMAT_VER, 1)

        else:
            sig_a = await x.load_uint(self.iobj, 4)
            sig_b = await x.load_uint(self.iobj, 4)
            ver = await x.load_uint(self.iobj, 1)

            if sig_a != PortableStorageConsts.SIGNATUREA:
                raise ValueError('Signature A error')
            if sig_b != PortableStorageConsts.SIGNATUREB:
                raise ValueError('Signature A error')
            if ver != PortableStorageConsts.FORMAT_VER:
                raise ValueError('Unsupported version')

    async def section(self, sec=None):
        """
        Section / dict serialization
        :return:
        """
        if self.writing:
            await dump_varint(self.iobj, len(sec))
            for key in sec:
                await self.section_name(key)
                await self.storage_entry(sec[key])

        else:
            sec = {} if sec is None else sec

            count = await load_varint(self.iobj)
            for idx in range(count):
                sec_name = await self.section_name()
                val = await self.storage_entry()
                sec[sec_name] = val

            return sec

    async def section_name(self, sec_name=None):
        """
        Section name
        :param sec_name:
        :return:
        """
        if self.writing:
            fvalue = sec_name.encode('ascii')
            await x.dump_uint(self.iobj, len(fvalue), 1)
            await self.iobj.awrite(bytearray(fvalue))

        else:
            ivalue = await x.load_uint(self.iobj, 1)
            fvalue = bytearray(ivalue)
            await self.iobj.areadinto(fvalue)
            return bytes(fvalue).decode('ascii')

    async def storage_entry(self, entry=None, ent_type=None):
        if self.writing:
            oentry = entry
            if ent_type is None:
                ent_type, entry = self.det_entry_model(entry)

            if ent_type & SerializeType.ARRAY_FLAG:
                return await self.entry(ent_type=ent_type, elem=oentry)

            else:
                await x.dump_uint(self.iobj, ent_type, 1)
                return await self.entry(ent_type=ent_type, elem=entry)

        else:
            ent_type = await x.load_uint(self.iobj, 1)
            return await self.entry(ent_type)

    async def array(self, container=None, container_type=None, params=None):
        if self.writing:
            if container_type is None and not isinstance(container, ArrayModel):
                raise ValueError('Unknown container type serialization')
            if container_type is None:
                container_type = container.type
                container = container.val

            entry_type = container_type & (~ SerializeType.ARRAY_FLAG)
            container_type |= SerializeType.ARRAY_FLAG

            await x.dump_uint(self.iobj, container_type, 1)
            await dump_varint(self.iobj, len(container))
            for i in container:
                await self.entry(entry_type, elem=i)

        else:
            if container_type is None:
                container_type = await x.load_uint(self.iobj, 1)

            container_type &= ~SerializeType.ARRAY_FLAG

            c_len = await load_varint(self.iobj)
            res = container if container else []
            for i in range(c_len):
                fval = await self.entry(container_type, x.eref(res, i) if container else None)
                if not container:
                    res.append(fval)

            return res if not self.modeled else ArrayModel(res, container_type)

    async def entry(self, ent_type, elem=None):
        if self.writing:
            oelem = elem
            elem = elem if not isinstance(elem, IModel) else elem.val

            if ent_type in SerializeTypeSize:
                return await x.dump_uint(self.iobj, elem, type_to_size(ent_type))
            elif ent_type == SerializeType.DUOBLE:
                raise ValueError('Not supported')
            elif ent_type == SerializeType.STRING:
                return await self.unicode_type(elem)
            elif ent_type == SerializeType.OBJECT:
                return await self.section(elem)
            elif ent_type == SerializeType.ARRAY:
                return await self.array(oelem)
            elif ent_type & SerializeType.ARRAY_FLAG:
                return await self.array(elem, container_type=ent_type & (~SerializeType.ARRAY_FLAG))
            else:
                raise ValueError('Unrecognized type 0x%x' % ent_type)

        else:
            if ent_type in SerializeTypeSize:
                fval = await x.load_uint(self.iobj, type_to_size(ent_type))
                return fval if not self.modeled else IntegerModel(fval, ent_type)
            elif ent_type == SerializeType.DUOBLE:
                raise ValueError('Not supported')
            elif ent_type == SerializeType.STRING:
                return await self.unicode_type()
            elif ent_type == SerializeType.OBJECT:
                return await self.section()
            elif ent_type == SerializeType.ARRAY:
                return await self.array()
            elif ent_type & SerializeType.ARRAY_FLAG:
                return await self.array(container_type=ent_type & (~SerializeType.ARRAY_FLAG))
            else:
                raise ValueError('Unrecognized type 0x%x' % ent_type)

    async def unicode_type(self, elem=None):
        if self.writing:
            return await dump_string(self.iobj, elem)

        else:
            return await load_string(self.iobj)

    @staticmethod
    def det_entry_model(entry):
        if isinstance(entry, IntegerModel):
            return entry.type, entry.val
        elif isinstance(entry, ArrayModel):
            return entry.type | SerializeType.ARRAY_FLAG, entry.val
        elif isinstance(entry, IModel):
            return entry.type, entry.val
        elif isinstance(entry, bytes):
            return SerializeType.STRING, entry
        elif isinstance(entry, bytearray):
            return SerializeType.STRING, bytes(entry)
        elif isinstance(entry, (dict, x.MessageType)):
            return SerializeType.OBJECT, entry
        elif isinstance(entry, (list, tuple)):
            return SerializeType.OBJECT | SerializeType.ARRAY_FLAG, entry  # fallback to obj
        else:
            raise ValueError('Unknown: %r' % entry)

