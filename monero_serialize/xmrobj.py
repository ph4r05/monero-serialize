#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Monero serialization to object representation.

Note: This is not optimized for memory usage. No streaming support.
Used for debugging.
'''

import base64
import collections

from . import xmrserialize as x
from .xmrserialize import eref, get_elem, set_elem


class Archive(x.Archive):
    """
    Archive object for object binary serialization / deserialization.
    Resembles Archive API from the Monero codebase or Boost serialization archive.

    The design goal is to provide uniform API both for serialization and deserialization
    so the code is not duplicated for serialization and deserialization but the same
    for both ways in order to minimize potential bugs in the code.

    In order to use the archive for both ways we have to use so-called field references
    as we cannot directly modify given element as a parameter (value-passing) as its performed
    in C++ code. see: eref(), get_elem(), set_elem()
    """
    def __init__(self, iobj, writing=True, **kwargs):
        super().__init__(iobj, writing, **kwargs)
        self.res = collections.OrderedDict()

    async def tag(self, tag):
        """
        TODO: implement
        :param tag:
        :return:
        """

    async def begin_array(self):
        """
        Mark start of the array. Used for JSON serialization.
        TODO: implement
        :return:
        """

    async def end_array(self):
        """
        Mark end of the array. Used for JSON serialization.
        TODO: implement
        :return:
        """

    async def begin_object(self):
        """
        Mark start of the object. Used for JSON serialization.
        TODO: implement
        :return:
        """

    async def end_object(self):
        """
        Mark end of the object. Used for JSON serialization.
        TODO: implement
        :return:
        """


async def dump_blob(elem, elem_type=None):
    """
    Dumps blob message.
    Supports both blob and raw value.

    :param writer:
    :param elem:
    :param elem_type:
    :param params:
    :return:
    """
    elem_is_blob = isinstance(elem, x.BlobType)
    data = getattr(elem, x.BlobType.DATA_ATTR) if elem_is_blob else elem
    if isinstance(data, (bytes, bytearray, list)):
        return base64.b16encode(data)
    else:
        raise ValueError('Unknown blob type')


async def load_blob(elem, elem_type=None):
    """
    Loads blob from serialized object
    :param elem:
    :return:
    """
    return base64.b16decode(elem)


async def dump_container(obj, container, container_type, params=None, field_archiver=None):
    """
    Serializes container as popo

    :param obj:
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

    obj = [] if obj is None else get_elem(obj)
    for elem in container:
        fvalue = await field_archiver(None, elem, elem_type, params[1:] if params else None)
        obj.append(fvalue)
    return obj


async def load_container(obj, container_type, params=None, container=None, field_archiver=None):
    """
    Loads container of elements from the object representation. Supports the container ref.
    Returns loaded container.

    :param reader:
    :param container_type:
    :param params:
    :param container:
    :param field_archiver:
    :return:
    """
    field_archiver = field_archiver if field_archiver else load_field

    c_len = len(obj)
    elem_type = params[0] if params else None
    if elem_type is None:
        elem_type = container_type.ELEM_TYPE

    res = container if container else []
    for i in range(c_len):
        fvalue = await field_archiver(obj[i], elem_type,
                                      params[1:] if params else None,
                                      eref(res, i) if container else None)
        if not container:
            res.append(fvalue)
    return res


async def dump_message_field(obj, msg, field, field_archiver=None):
    """
    Dumps a message field to the object. Field is defined by the message field specification.

    :param obj:
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
    return await field_archiver(eref(obj, fname, True), fvalue, ftype, params)


async def load_message_field(obj, msg, field, field_archiver=None):
    """
    Loads message field from the object. Field is defined by the message field specification.
    Returns loaded value, supports field reference.

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
    await field_archiver(obj[fname], ftype, params, eref(msg, fname))


async def dump_message(obj, msg, field_archiver=None):
    """
    Dumps message to the object.
    Returns message popo representation.

    :param obj:
    :param msg:
    :param field_archiver:
    :return:
    """
    mtype = msg.__class__
    fields = mtype.FIELDS

    obj = collections.OrderedDict() if obj is None else get_elem(obj)
    for field in fields:
        await dump_message_field(obj, msg=msg, field=field, field_archiver=field_archiver)
    return obj


async def load_message(obj, msg_type, msg=None, field_archiver=None):
    """
    Loads message if the given type from the object.
    Supports reading directly to existing message.

    :param obj:
    :param msg_type:
    :param msg:
    :param field_archiver:
    :return:
    """
    msg = msg_type() if msg is None else msg

    fields = msg_type.FIELDS if msg_type else msg.__class__.FIELDS
    for field in fields:
        await load_message_field(obj, msg, field, field_archiver=field_archiver)

    return msg


async def dump_variant(obj, elem, elem_type=None, params=None, field_archiver=None):
    """
    Transform variant to the popo object representation.

    :param obj:
    :param elem:
    :param elem_type:
    :param params:
    :param field_archiver:
    :return:
    """
    field_archiver = field_archiver if field_archiver else dump_field
    if isinstance(elem, x.VariantType) or elem_type.WRAPS_VALUE:
        return {
            elem.variant_elem: await field_archiver(None, getattr(elem, elem.variant_elem), elem.variant_elem_type)
        }

    else:
        fdef = elem_type.find_fdef(elem_type.FIELDS, elem)
        return {
            fdef[0]: await field_archiver(None, elem, fdef[1])
        }


async def load_variant(obj, elem, elem_type=None, params=None, field_archiver=None, wrapped=None):
    """
    Loads variant from the obj representation
    :param obj:
    :param elem:
    :param elem_type:
    :param params:
    :param field_archiver:
    :param wrapped:
    :return:
    """
    field_archiver = field_archiver if field_archiver else load_field
    is_wrapped = elem_type.WRAPS_VALUE if wrapped is None else wrapped

    if is_wrapped:
        elem = elem_type() if elem is None else elem

    fname = list(obj.keys())[0]
    for field in elem_type.FIELDS:
        if field[0] != fname:
            continue

        fvalue = await field_archiver(obj[fname], field[1], field[2:], elem if not is_wrapped else None)
        if is_wrapped:
            elem.set_variant(field[0], fvalue)

        return elem if is_wrapped else fvalue
    raise ValueError('Unknown tag: %s' % fname)


async def dump_field(obj, elem, elem_type, params=None):
    """
    Dumps generic field to the popo object representation, according to the element specification.
    General multiplexer.

    :param obj:
    :param elem:
    :param elem_type:
    :param params:
    :return:
    """
    if isinstance(elem, (int, bool)) or issubclass(elem_type, x.UVarintType) or issubclass(elem_type, x.IntType):
        return set_elem(obj, elem)

    elif issubclass(elem_type, x.BlobType) or isinstance(obj, bytes) or isinstance(obj, bytearray):
        return set_elem(obj, await dump_blob(elem))

    elif issubclass(elem_type, x.UnicodeType) or isinstance(elem, str):
        return set_elem(obj, elem)

    elif issubclass(elem_type, x.VariantType):
        return set_elem(obj, await dump_variant(None, elem, elem_type, params))

    elif issubclass(elem_type, x.ContainerType):  # container ~ simple list
        return set_elem(obj, await dump_container(None, elem, elem_type, params))

    elif issubclass(elem_type, x.MessageType):
        return set_elem(obj, await dump_message(None, elem))

    else:
        raise TypeError


async def load_field(obj, elem_type, params=None, elem=None):
    """
    Loads a field from the reader, based on the field type specification. Demultiplexer.

    :param obj:
    :param elem_type:
    :param params:
    :param elem:
    :return:
    """
    if issubclass(elem_type, x.UVarintType) or issubclass(elem_type, x.IntType) or isinstance(obj, (int, bool)):
        return set_elem(elem, obj)

    elif issubclass(elem_type, x.BlobType):
        fvalue = await load_blob(obj, elem_type)
        return set_elem(elem, fvalue)

    elif issubclass(elem_type, x.UnicodeType) or isinstance(elem, str):
        return set_elem(elem, obj)

    elif issubclass(elem_type, x.VariantType):
        fvalue = await load_variant(obj, elem=get_elem(elem), elem_type=elem_type, params=params)
        return set_elem(elem, fvalue)

    elif issubclass(elem_type, x.ContainerType):  # container ~ simple list
        fvalue = await load_container(obj, elem_type, params=params, container=get_elem(elem))
        return set_elem(elem, fvalue)

    elif issubclass(elem_type, x.MessageType):
        fvalue = await load_message(obj, msg_type=elem_type, msg=get_elem(elem))
        return set_elem(elem, fvalue)

    else:
        raise TypeError


