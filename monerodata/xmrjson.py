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

from .protobuf import const, load_uvarint, dump_uvarint, LimitedReader, CountingWriter
from . import xmrserialize as x
from .xmrserialize import eref, get_elem, set_elem


class Archive(x.Archive):

    def __init__(self, iobj, writing=True, **kwargs):
        super().__init__(iobj, writing, **kwargs)


class AutoJSONEncoder(json.JSONEncoder):
    """
    JSON encoder trying to_json() first
    """
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

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


async def dump_blob(elem):
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
    if isinstance(data, bytes):
        return base64.b16encode(data)
    elif isinstance(data, (bytearray, list)):
        return base64.b16encode(data)
    else:
        raise ValueError('Unknown blob type')


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
    return [await field_archiver(None, elem, elem_type, params[1:] if params else None) for elem in container]


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



