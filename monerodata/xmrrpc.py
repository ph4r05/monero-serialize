#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
XMR RPC serialization

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

...Not finished yet...
'''


from . import xmrserialize as x
from .xmrserialize import eref


_UINT_BUFFER = bytearray(1)


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
        return dump_varint_t(writer, PortableRawSizeMark.BYTE, val)
    elif val <= 16383:
        return dump_varint_t(writer, PortableRawSizeMark.WORD, val)
    elif val <= 1073741823:
        return dump_varint_t(writer, PortableRawSizeMark.DWORD, val)
    else:
        if val > 4611686018427387903:
            raise ValueError('Int too big')
        return dump_varint_t(writer, PortableRawSizeMark.INT64, val)


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
    await writer.awrite(bytes(val, 'utf8'))


async def load_string(reader):
    """
    Loads string from binary stream

    :param reader:
    :return:
    """
    ivalue = await load_varint(reader)
    fvalue = bytearray(ivalue)
    await reader.areadinto(fvalue)
    fvalue = str(fvalue, 'utf8')
    return fvalue


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


async def dump_container(writer, container, container_type, params=None, field_archiver=None):
    """
    Dumps container of elements to the writer.

    :param writer:
    :param container:
    :param container_type:
    :param params:
    :param field_archiver:
    :return:
    """
    field_archiver = field_archiver if field_archiver else dump_field
    elem_type = params[0] if params else None
    if elem_type is None:
        elem_type = container_type.ELEM_TYPE

    type_code = xmr_type_to_type(elem_type) | SerializeType.ARRAY_FLAG
    buff = bytearray(1)
    buff[0] = type_code
    await writer.awrite(buff)
    await dump_varint(writer, len(container))

    for elem in container:
        await field_archiver(writer, elem, elem_type, params[1:] if params else None)


#
# Code needs some check below this point
#


async def load_container(reader, container_type, params=None, container=None, field_archiver=None):
    """
    Loads container of elements from the reader. Supports the container ref.
    Returns loaded container.
    TODO: implement

    :param reader:
    :param container_type:
    :param params:
    :param container:
    :param field_archiver:
    :return:
    """
    field_archiver = field_archiver if field_archiver else load_field

    c_len = container_type.SIZE if container_type.FIX_SIZE else await load_varint(reader)
    if container and c_len != len(container):
        raise ValueError('Size mismatch')

    elem_type = params[0] if params else None
    if elem_type is None:
        elem_type = container_type.ELEM_TYPE

    res = container if container else []
    for i in range(c_len):
        fvalue = await field_archiver(reader, elem_type,
                                      params[1:] if params else None,
                                      eref(res, i) if container else None)
        if not container:
            res.append(fvalue)
    return res


async def dump_message_field(writer, msg, field, field_archiver=None):
    """
    Dumps a message field to the writer. Field is defined by the message field specification.
    TODO: implement

    :param writer:
    :param msg:
    :param field:
    :param field_archiver:
    :return:
    """
    fname = field[0]
    ftype = field[1]
    params = field[2:]

    fvalue = getattr(msg, fname, None)
    field_archiver = field_archiver if field_archiver else dump_field
    await field_archiver(writer, fvalue, ftype, params)


async def load_message_field(reader, msg, field, field_archiver=None):
    """
    Loads message field from the reader. Field is defined by the message field specification.
    Returns loaded value, supports field reference.
    TODO: implement

    :param reader:
    :param msg:
    :param field:
    :param field_archiver:
    :return:
    """
    fname = field[0]
    ftype = field[1]
    params = field[2:]

    field_archiver = field_archiver if field_archiver else load_field
    await field_archiver(reader, ftype, params, eref(msg, fname))


async def dump_message(writer, msg, field_archiver=None):
    """
    Dumps message to the writer.
    TODO: implement

    :param writer:
    :param msg:
    :param field_archiver:
    :return:
    """
    mtype = msg.__class__
    fields = mtype.FIELDS

    for field in fields:
        await dump_message_field(writer, msg=msg, field=field, field_archiver=field_archiver)


async def load_message(reader, msg_type, msg=None, field_archiver=None):
    """
    Loads message if the given type from the reader.
    Supports reading directly to existing message.
    TODO: implement

    :param reader:
    :param msg_type:
    :param msg:
    :param field_archiver:
    :return:
    """
    msg = msg_type() if msg is None else msg
    fields = msg_type.FIELDS if msg_type else msg.__class__.FIELDS
    for field in fields:
        await load_message_field(reader, msg, field, field_archiver=field_archiver)

    return msg


async def dump_field(writer, elem, elem_type, params=None):
    """
    TODO: implement

    :param writer:
    :param elem:
    :param elem_type:
    :param params:
    :return:
    """
    if issubclass(elem_type, x.UVarintType) or issubclass(elem_type, x.IntType) \
            or (elem_type is None and isinstance(elem, int)):
        await dump_varint(writer, elem)

    elif issubclass(elem_type, x.BlobType):
        await dump_blob(writer, elem, elem_type, params)

    elif issubclass(elem_type, x.UnicodeType):
        await dump_string(writer, elem)

    elif issubclass(elem_type, x.ContainerType):  # container ~ simple list
        await dump_container(writer, elem, elem_type, params)

    elif issubclass(elem_type, x.MessageType):
        await dump_message(writer, elem)

    else:
        raise TypeError


async def load_field(reader, elem_type, params=None, elem=None):
    """
    Loads a field from the reader, based on the field type specification. Demultiplexer.
    TODO: implement

    :param reader:
    :param elem_type:
    :param params:
    :param elem:
    :return:
    """
    if issubclass(elem_type, x.UVarintType) or issubclass(elem_type, x.IntType) \
            or (elem_type is None and isinstance(elem, int)):
        fvalue = await load_varint(reader)
        return x.set_elem(elem, fvalue)

    elif issubclass(elem_type, x.UnicodeType):
        fvalue = await load_string(reader)
        return x.set_elem(elem, fvalue)

    elif issubclass(elem_type, x.ContainerType):  # container ~ simple list
        fvalue = await load_container(reader, elem_type, params=params, container=x.get_elem(elem))
        return x.set_elem(elem, fvalue)

    elif issubclass(elem_type, x.MessageType):
        fvalue = await load_message(reader, msg_type=elem_type, msg=x.get_elem(elem))
        return x.set_elem(elem, fvalue)

    else:
        raise TypeError



