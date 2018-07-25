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
import collections

from . import xmrserialize as x
from . import helpers
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
    x.BlobType: SerializeType.STRING,
}


class BlobFieldWrapper(object):
    """Given field should be serialized/unserialized as blob"""
    def __init__(self, ftype, *args, **kwargs):
        self.ftype = ftype


class DefaultFieldWrapper(object):
    """Returns default if not set"""
    def __init__(self, ftype, default=None, *args, **kwargs):
        self.ftype = ftype
        self.default = default


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


class BlobModel(IModel):
    def __str__(self):
        return 'Blob[%s; %s]' % (self.type, self.val)


class NoSetSentinel(object):
    pass


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
    elif elem_type == object or elem_type == type:
        raise ValueError('Canot convert Xmr type: %s' % elem_type)
    elif elem_type in XmrTypeMap:
        return XmrTypeMap[elem_type]
    elif isinstance(elem_type, x.XmrType) and elem_type.__class__ in XmrTypeMap:
        return XmrTypeMap[elem_type.__class__]
    elif len(elem_type.__bases__) > 0:
        return xmr_type_to_type(elem_type.__bases__[0])
    else:
        raise ValueError('Cannot convert Xmr type %s' % elem_type)


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
    data = bytes(getattr(elem, x.BlobType.DATA_ATTR) if elem_is_blob else elem)
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


#
# Blob serializer
#

class Blobber(object):
    """
    Serializing structures to Blob for KV_SERIALIZE.
    """
    def __init__(self, iobj=None, writing=True, data=None, **kwargs):
        self.writing = writing
        self.tracker = helpers.Tracker()
        self.iobj = x.MemoryReaderWriter() if iobj is not None else iobj
        if data is not None:
            self.iobj = x.MemoryReaderWriter(bytearray(data))

    async def uvarint(self, elem):
        """
        Uvarint untouched
        :param elem:
        :return:
        """
        if self.writing:
            return await dump_varint(self.iobj, elem)
        else:
            return await load_varint(self.iobj)

    async def uint(self, elem, elem_type, params=None):
        """
        Integer types
        :param elem:
        :param elem_type:
        :param params:
        :return:
        """
        if self.writing:
            return await x.dump_uint(self.iobj, elem, elem_type.WIDTH)
        else:
            return await x.load_uint(self.iobj, elem_type.WIDTH)

    async def unicode_type(self, elem):
        """
        Unicode type
        :param elem:
        :return:
        """
        if self.writing:
            return await x.dump_unicode(self.iobj, elem)
        else:
            return await x.load_unicode(self.iobj)

    async def blob(self, elem=None, elem_type=None, params=None):
        """
        Loads/dumps blob
        :return:
        """
        elem_type = elem_type if elem_type else elem.__class__
        if hasattr(elem_type, 'blob_serialize'):
            elem = elem_type() if elem is None else elem
            return await elem.blob_serialize(self, elem=elem, elem_type=elem_type, params=params)

        if self.writing:
            return await x.dump_blob(self.iobj, elem=elem, elem_type=elem_type, params=params)
        else:
            return await x.load_blob(self.iobj, elem_type=elem_type, params=params, elem=elem)

    async def container(self, container=None, container_type=None, params=None):
        """
        Loads/dumps container
        :return:
        """
        if hasattr(container_type, 'blob_serialize'):
            container = container_type() if container is None else container
            return await container.blob_serialize(self, elem=container, elem_type=container_type, params=params)

        # Container entry version + container
        if self.writing:
            return await self.container_dump(container, container_type, params)
        else:
            return await self.container_load(container_type, params=params, container=container)

    async def get_element_size(self, elem_type, elem=None, params=None):
        """
        Determines element size after blob serialization.
        Can be quite tricky for complicated structures - another object required to implement sizeof()

        :param elem_type:
        :param elem:
        :param params:
        :return:
        """
        if hasattr(elem_type, 'blob_size'):
            elem = elem_type() if elem is None else elem
            return await elem.blob_size(self)

        if issubclass(elem_type, x.UVarintType):
            raise helpers.ArchiveException('Unknown size for varint')

        elif issubclass(elem_type, x.IntType):
            return elem_type.WIDTH

        elif issubclass(elem_type, x.BlobType):
            if elem is not None:
                return len(elem)
            if not elem_type.FIX_SIZE:
                raise helpers.ArchiveException('Unknown size for blob')
            return elem_type.SIZE

        elif issubclass(elem_type, x.UnicodeType):
            raise helpers.ArchiveException('Unknown size for string')

        elif issubclass(elem_type, x.VariantType):
            raise helpers.ArchiveException('Unknown size for variant')

        elif issubclass(elem_type, x.ContainerType):  # container ~ simple list
            celem_type = x.container_elem_type(elem_type, params)
            if elem is not None:
                return len(elem) * await self.get_element_size(elem_type=celem_type, elem=elem[0] if len(elem) > 0 else None)
            if not elem_type.FIX_SIZE:
                raise helpers.ArchiveException('Unknown size for container')
            return elem_type.SIZE * await self.get_element_size(elem_type=celem_type)

        elif issubclass(elem_type, x.TupleType):  # tuple ~ simple list
            acc = 0
            for t in elem_type.f_specs():
                acc += await self.get_element_size(t)
            return acc

        elif issubclass(elem_type, x.MessageType):
            acc = 0
            for t in elem_type.f_specs():
                acc += await self.get_element_size(t[1], params=t[2:])
            return acc

        else:
            raise TypeError

    async def container_dump(self, container, container_type, params=None):
        """
        Dumps container of elements to the writer.
        Blob array writer as in XMRRPC is serialized without size serialization

        :param container:
        :param container_type:
        :param params:
        :param obj:
        :return:
        """
        elem_type = x.container_elem_type(container_type, params)
        if container is None:
            return

        for idx, elem in enumerate(container):
            try:
                self.tracker.push_index(idx)
                await self._dump_field(elem, elem_type, params[1:] if params else None)
                self.tracker.pop()
            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

    async def container_load(self, container_type, params=None, container=None, obj=None):
        """
        Loads container of elements from the reader. Supports the container ref.
        Returns loaded container.
        Blob array writer as in XMRRPC is serialized without size serialization.

        :param container_type:
        :param params:
        :param container:
        :param obj:
        :return:
        """
        elem_type = x.container_elem_type(container_type, params)
        elem_size = await self.get_element_size(elem_type=elem_type, params=params)

        # If container is of fixed size we know the size to load from the input.
        # Otherwise we have to read to the end
        data_left = len(self.iobj.buffer)
        c_len = container_type.SIZE
        if not container_type.FIX_SIZE:
            if data_left == 0:
                return None
            if data_left % elem_size != 0:
                raise helpers.ArchiveException('Container size mod elem size not 0')
            c_len = data_left // elem_size

        res = container if container else []
        for i in range(c_len):
            try:
                self.tracker.push_index(i)
                fvalue = await self._load_field(elem_type,
                                                params[1:] if params else None,
                                                x.eref(res, i) if container else None)
                self.tracker.pop()
            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

            if not container:
                res.append(fvalue)
        return res

    async def tuple(self, elem=None, elem_type=None, params=None):
        """
        Loads/dumps tuple
        :return:
        """
        if hasattr(elem_type, 'blob_serialize'):
            container = elem_type() if elem is None else elem
            return await container.blob_serialize(self, elem=elem, elem_type=elem_type, params=params)

        if self.writing:
            return await self.dump_tuple(elem, elem_type, params)
        else:
            return await self.load_tuple(elem_type, params=params, elem=elem)

    async def dump_tuple(self, elem, elem_type, params=None, obj=None):
        """
        Dumps tuple of elements to the writer.

        :param elem:
        :param elem_type:
        :param params:
        :param obj:
        :return:
        """
        raise helpers.ArchiveException('Not yet implemented')

    async def load_tuple(self, elem_type, params=None, elem=None, obj=None):
        """
        Loads tuple of elements from the reader. Supports the tuple ref.
        Returns loaded tuple.

        :param elem_type:
        :param params:
        :param elem:
        :param obj:
        :return:
        """
        raise helpers.ArchiveException('Not yet implemented')

    async def variant(self, elem=None, elem_type=None, params=None):
        """
        Loads/dumps variant type
        :param elem:
        :param elem_type:
        :param params:
        :param obj:
        :return:
        """
        elem_type = elem_type if elem_type else elem.__class__

        if hasattr(elem_type, 'blob_serialize'):
            elem = elem_type() if elem is None else elem
            return await elem.bob_serialize(self, elem=elem, elem_type=elem_type, params=params)

        if self.writing:
            return await self.dump_variant(elem=elem,
                                           elem_type=elem_type if elem_type else elem.__class__, params=params)
        else:
            return await self.load_variant(elem_type=elem_type if elem_type else elem.__class__,
                                           params=params, elem=elem)

    async def dump_variant(self, elem, elem_type=None, params=None, obj=None):
        """
        Dumps variant type to the writer.
        Supports both wrapped and raw variant.

        :param elem:
        :param elem_type:
        :param params:
        :param obj:
        :return:
        """
        raise helpers.ArchiveException('Not yet implemented')

    async def load_variant(self, elem_type, params=None, elem=None, wrapped=None, obj=None):
        """
        Loads variant type from the reader.
        Supports both wrapped and raw variant.

        :param elem_type:
        :param params:
        :param elem:
        :param wrapped:
        :param obj:
        :return:
        """
        raise helpers.ArchiveException('Not yet implemented')

    async def message(self, msg, msg_type=None):
        """
        Loads/dumps message
        :param msg:
        :param msg_type:
        :param obj:
        :return:
        """
        elem_type = msg_type if msg_type is not None else msg.__class__

        if hasattr(elem_type, 'blob_serialize'):
            msg = elem_type() if msg is None else msg
            return await msg.blob_serialize(self)

        fields = elem_type.f_specs()
        for field in fields:
            await self.message_field(msg=msg, field=field)

        return msg

    async def message_field(self, msg, field, fvalue=None, obj=None):
        """
        Dumps/Loads message field
        :param msg:
        :param field:
        :param fvalue: explicit value for dump
        :param obj:
        :return:
        """
        fname, ftype, params = field[0], field[1], field[2:]
        try:
            self.tracker.push_field(fname)
            if self.writing:
                fvalue = getattr(msg, fname, None) if fvalue is None else fvalue
                await self._dump_field(fvalue, ftype, params)

            else:
                await self._load_field(ftype, params, x.eref(msg, fname))

            self.tracker.pop()

        except Exception as e:
            raise helpers.ArchiveException(e, tracker=self.tracker) from e

    async def message_fields(self, msg, fields, obj=None):
        """
        Load/dump individual message fields
        :param msg:
        :param fields:
        :param obj:
        :return:
        """
        for field in fields:
            await self.message_field(msg, field, obj)
        return msg

    async def field(self, elem=None, elem_type=None, params=None):
        """
        Archive field
        :param elem:
        :param elem_type:
        :param params:
        :return:
        """
        elem_type = elem_type if elem_type else elem.__class__
        fvalue = None

        src = elem
        if issubclass(elem_type, x.UVarintType):
            fvalue = await self.uvarint(x.get_elem(src))

        elif issubclass(elem_type, x.IntType):
            fvalue = await self.uint(elem=x.get_elem(src), elem_type=elem_type, params=params)

        elif issubclass(elem_type, x.BlobType):
            fvalue = await self.blob(elem=x.get_elem(src), elem_type=elem_type, params=params)

        elif issubclass(elem_type, x.UnicodeType):
            fvalue = await self.unicode_type(x.get_elem(src))

        elif issubclass(elem_type, x.VariantType):
            fvalue = await self.variant(elem=x.get_elem(src), elem_type=elem_type, params=params)

        elif issubclass(elem_type, x.ContainerType):  # container ~ simple list
            fvalue = await self.container(container=x.get_elem(src), container_type=elem_type, params=params)

        elif issubclass(elem_type, x.TupleType):  # tuple ~ simple list
            fvalue = await self.tuple(elem=x.get_elem(src), elem_type=elem_type, params=params)

        elif issubclass(elem_type, x.MessageType):
            fvalue = await self.message(x.get_elem(src), msg_type=elem_type)

        else:
            raise TypeError

        return fvalue if self.writing else x.set_elem(elem, fvalue)

    async def _dump_field(self, elem, elem_type, params=None):
        return await self.field(elem=elem, elem_type=elem_type, params=params)

    async def _load_field(self, elem_type, params=None, elem=None):
        return await self.field(elem=elem, elem_type=elem_type, params=params)

    async def blobize(self, elem=None, elem_type=None, params=None):
        """
        Main blobbing
        :param elem:
        :param elem_type:
        :param params:
        :return:
        """
        if self.writing:
            await self.field(elem=elem, elem_type=elem_type, params=params)
            return bytes(self.iobj.buffer)
        else:
            return await self.field(elem=elem, elem_type=elem_type, params=params)


class Modeler(object):
    """
    Converting message classes to models and vice versa.
    Writing  = transforming message to model.
    !Writing = transforming model to message.
    """

    def __init__(self, writing=True, hexlify=False, modelize=True, strict_load=False, **kwargs):
        self.writing = writing
        self.hexlify = hexlify
        self.modelize = modelize
        self.strict_load = strict_load
        self.tracker = helpers.Tracker()

    @staticmethod
    def to_bytes(elem):
        if isinstance(elem, bytearray):
            return bytes(elem)
        if isinstance(elem, str):
            return elem.encode('utf8')
        if isinstance(elem, list):
            return bytes(elem)
        return elem

    async def uvarint(self, elem):
        """
        Uvarint untouched
        :param elem:
        :return:
        """
        return elem

    async def uint(self, elem, elem_type, params=None):
        """
        Integer types
        :param elem:
        :param elem_type:
        :param params:
        :return:
        """
        if self.writing:
            return IntegerModel(elem, elem_type.WIDTH) if self.modelize else elem
        else:
            return elem.val if isinstance(elem, IModel) else elem

    async def unicode_type(self, elem):
        """
        Unicode type
        :param elem:
        :return:
        """
        if self.writing:
            return Modeler.to_bytes(elem)

        else:
            return elem

    async def blob(self, elem=None, elem_type=None, params=None):
        """
        Loads/dumps blob
        :return:
        """
        elem_type = elem_type if elem_type else elem.__class__
        if hasattr(elem_type, 'kv_serialize'):
            elem = elem_type() if elem is None else elem
            return await elem.kv_serialize(self, elem=elem, elem_type=elem_type, params=params)

        if self.writing:
            elem_is_blob = isinstance(elem, x.BlobType)
            data = getattr(elem, x.BlobType.DATA_ATTR) if elem_is_blob else elem
            if data is None:
                return NoSetSentinel()
            if len(data) == 0:
                return b''

            fval = Modeler.to_bytes(data)
            if self.hexlify:
                return binascii.hexlify(fval).decode('ascii')
            else:
                return fval

        else:
            if elem is None:
                return NoSetSentinel()
            if self.hexlify:
                return bytes(binascii.unhexlify(elem))
            else:
                return bytes(elem)

    async def container(self, container=None, container_type=None, params=None, obj=None):
        """
        Loads/dumps container
        :return:
        """
        if hasattr(container_type, 'kv_serialize'):
            container = container_type() if container is None else container
            return await container.kv_serialize(self, elem=container, elem_type=container_type, params=params, obj=obj)

        # Container entry version + container
        if self.writing:
            return await self.container_dump(container, container_type, params, obj=obj)
        else:
            return await self.container_load(container_type, params=params, container=container, obj=obj)

    async def container_dump(self, container, container_type, params=None, obj=None):
        """
        Dumps container of elements to the writer.

        :param container:
        :param container_type:
        :param params:
        :param obj:
        :return:
        """
        elem_type = x.container_elem_type(container_type, params)
        obj = [] if not x.has_elem(obj) else x.get_elem(obj)

        # todo: pod container, just concat blobs / serialized content together. loading = size / elem size...
        if container is None:  # todo: reconsider
            return NoSetSentinel()  # if not self.modelize else ArrayModel(obj, xmr_type_to_type(elem_type))

        for idx, elem in enumerate(container):
            try:
                self.tracker.push_index(idx)
                fvalue = await self._dump_field(elem, elem_type, params[1:] if params else None)
                self.tracker.pop()

            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

            if not isinstance(fvalue, NoSetSentinel):
                obj.append(fvalue)

        return obj if not self.modelize else ArrayModel(obj, xmr_type_to_type(elem_type))

    async def container_load(self, container_type, params=None, container=None, obj=None):
        """
        Loads container of elements from the reader. Supports the container ref.
        Returns loaded container.

        :param container_type:
        :param params:
        :param container:
        :param obj:
        :return:
        """
        if isinstance(obj, IModel):
            obj = obj.val

        if obj is None:
            return NoSetSentinel()

        c_len = len(obj)
        elem_type = params[0] if params else None
        if elem_type is None:
            elem_type = container_type.ELEM_TYPE

        res = container if container else []
        for i in range(c_len):
            try:
                self.tracker.push_index(i)
                fvalue = await self._load_field(elem_type,
                                                params[1:] if params else None,
                                                x.eref(res, i) if container else None, obj=obj[i])
                self.tracker.pop()

            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

            if not container and not isinstance(fvalue, NoSetSentinel):
                res.append(fvalue)

        return res

    async def tuple(self, elem=None, elem_type=None, params=None, obj=None):
        """
        Loads/dumps tuple
        :return:
        """
        if hasattr(elem_type, 'kv_serialize'):
            container = elem_type() if elem is None else elem
            return await container.kv_serialize(self, elem=elem, elem_type=elem_type, params=params, obj=obj)

        # TODO: if modeled return as 0=>, 1=>, ...
        if self.writing:
            return await self.dump_tuple(elem, elem_type, params, obj=obj)
        else:
            return await self.load_tuple(elem_type, params=params, elem=elem, obj=obj)

    async def dump_tuple(self, elem, elem_type, params=None, obj=None):
        """
        Dumps tuple of elements to the writer.

        :param elem:
        :param elem_type:
        :param params:
        :param obj:
        :return:
        """
        if len(elem) != len(elem_type.f_specs()):
            raise ValueError('Fixed size tuple has not defined size: %s' % len(elem_type.f_specs()))

        elem_fields = params[0] if params else None
        if elem_fields is None:
            elem_fields = elem_type.f_specs()

        obj = [] if obj is None else x.get_elem(obj)
        for idx, elem in enumerate(elem):
            try:
                self.tracker.push_index(idx)
                fvalue = await self._dump_field(elem, elem_fields[idx], params[1:] if params else None)
                obj.append(fvalue)
                self.tracker.pop()

            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

        return obj

    async def load_tuple(self, elem_type, params=None, elem=None, obj=None):
        """
        Loads tuple of elements from the reader. Supports the tuple ref.
        Returns loaded tuple.

        :param elem_type:
        :param params:
        :param elem:
        :param obj:
        :return:
        """
        if obj is None:
            return None

        elem_fields = params[0] if params else None
        if elem_fields is None:
            elem_fields = elem_type.f_specs()

        c_len = len(obj)
        if len(elem_fields) != c_len:
            raise ValueError('Size mismatch')

        res = elem if elem else []
        for i in range(len(elem_fields)):
            try:
                self.tracker.push_index(i)
                fvalue = await self._load_field(params[1:] if params else None,
                                                x.eref(res, i) if elem else None,
                                                obj=obj[i])
                self.tracker.pop()

                if not elem:
                    res.append(fvalue)

            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

        return res

    async def variant(self, elem=None, elem_type=None, params=None, obj=None):
        """
        Loads/dumps variant type
        :param elem:
        :param elem_type:
        :param params:
        :param obj:
        :return:
        """
        elem_type = elem_type if elem_type else elem.__class__

        if hasattr(elem_type, 'kv_serialize'):
            elem = elem_type() if elem is None else elem
            return await elem.kv_serialize(self, elem=elem, elem_type=elem_type, params=params, obj=obj)

        if self.writing:
            return await self.dump_variant(elem=elem,
                                           elem_type=elem_type if elem_type else elem.__class__, params=params, obj=obj)
        else:
            return await self.load_variant(elem_type=elem_type if elem_type else elem.__class__,
                                           params=params, elem=elem, obj=obj)

    async def dump_variant(self, elem, elem_type=None, params=None, obj=None):
        """
        Dumps variant type to the writer.
        Supports both wrapped and raw variant.

        :param elem:
        :param elem_type:
        :param params:
        :param obj:
        :return:
        """
        fvalue = None
        if isinstance(elem, x.VariantType) or elem_type.WRAPS_VALUE:
            try:
                self.tracker.push_variant(elem.variant_elem_type)
                fvalue = {
                    elem.variant_elem: await self._dump_field(getattr(elem, elem.variant_elem), elem.variant_elem_type, obj=obj)
                }
                self.tracker.pop()

            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

        else:
            try:
                fdef = elem_type.find_fdef(elem_type.f_specs(), elem)
                self.tracker.push_variant(fdef[1])
                fvalue = {
                    fdef[0]: await self._dump_field(elem, fdef[1], obj=obj)
                }
                self.tracker.pop()

            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

        return fvalue

    async def load_variant(self, elem_type, params=None, elem=None, wrapped=None, obj=None):
        """
        Loads variant type from the reader.
        Supports both wrapped and raw variant.

        :param elem_type:
        :param params:
        :param elem:
        :param wrapped:
        :param obj:
        :return:
        """
        is_wrapped = elem_type.WRAPS_VALUE if wrapped is None else wrapped

        if is_wrapped:
            elem = elem_type() if elem is None else elem

        fname = list(obj.keys())[0]
        for field in elem_type.f_specs():
            if field[0] != fname:
                continue

            try:
                self.tracker.push_variant(field[1])
                fvalue = await self._load_field(field[1], field[2:], elem if not is_wrapped else None, obj=obj[fname])
                self.tracker.pop()

            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

            if is_wrapped:
                elem.set_variant(field[0], fvalue)

            return elem if is_wrapped else fvalue
        raise ValueError('Unknown tag: %s' % fname)

    async def message(self, msg, msg_type=None, obj=None):
        """
        Loads/dumps message
        :param msg:
        :param msg_type:
        :param obj:
        :return:
        """
        elem_type = msg_type if msg_type is not None else msg.__class__
        obj = collections.OrderedDict() if not x.has_elem(obj) else x.get_elem(obj)

        if hasattr(elem_type, 'kv_serialize'):
            msg = elem_type() if msg is None else msg
            return await msg.kv_serialize(self, obj=obj)

        fields = elem_type.f_specs()
        for field in fields:
            await self.message_field(msg=msg, field=field, obj=obj)

        return obj if self.writing else msg

    async def message_field(self, msg, field, fvalue=None, obj=None):
        """
        Dumps/Loads message field
        :param msg:
        :param field:
        :param fvalue: explicit value for dump
        :param obj:
        :return:
        """
        fname, ftype, params = field[0], field[1], field[2:]

        try:
            self.tracker.push_field(field[0])

            if self.writing:
                if msg is None:
                    return None
                fvalue = getattr(msg, fname, None) if fvalue is None else fvalue
                await self._dump_field(fvalue, ftype, params, obj=eref(obj, fname, True))
            else:
                oval = obj[fname] if self.strict_load else (obj[fname] if fname in obj else None)
                await self._load_field(ftype, params, x.eref(msg, fname), obj=oval)

            self.tracker.pop()

        except Exception as e:
            raise helpers.ArchiveException(e, tracker=self.tracker) from e

    async def message_fields(self, msg, fields, obj=None):
        """
        Load/dump individual message fields
        :param msg:
        :param fields:
        :param obj:
        :return:
        """
        for field in fields:
            await self.message_field(msg, field, obj)
        return msg

    async def field(self, elem=None, elem_type=None, params=None, obj=None):
        """
        Archive field
        :param elem:
        :param elem_type:
        :param params:
        :param obj:
        :return:
        """
        elem_type = elem_type if elem_type else elem.__class__
        fvalue = None

        src = elem if self.writing else obj
        dst = obj if self.writing else elem

        # TODO: optional elem, default value for deserialization...

        # Blob wrapper. Underlying structure should be serialized as blob.
        if x.is_type(elem_type, BlobFieldWrapper):
            blobber = Blobber(self.writing, data=x.get_elem(src) if not self.writing else None)
            fvalue = await blobber.blobize(elem=x.get_elem(src), elem_type=elem_type.ftype, params=params)
            fvalue = NoSetSentinel() if fvalue is None or len(fvalue) == 0 else fvalue

        elif issubclass(elem_type, x.UVarintType):
            fvalue = await self.uvarint(x.get_elem(src))

        elif issubclass(elem_type, x.IntType):
            fvalue = await self.uint(elem=x.get_elem(src), elem_type=elem_type, params=params)

        elif issubclass(elem_type, x.BlobType):
            fvalue = await self.blob(elem=x.get_elem(src), elem_type=elem_type, params=params)

        elif issubclass(elem_type, x.UnicodeType):
            fvalue = await self.unicode_type(x.get_elem(src))

        elif issubclass(elem_type, x.VariantType):
            fvalue = await self.variant(elem=x.get_elem(src), elem_type=elem_type, params=params, obj=dst)

        elif issubclass(elem_type, x.ContainerType):  # container ~ simple list
            fvalue = await self.container(container=x.get_elem(src), container_type=elem_type, params=params, obj=dst)

        elif issubclass(elem_type, x.TupleType):  # tuple ~ simple list
            fvalue = await self.tuple(elem=x.get_elem(src), elem_type=elem_type, params=params, obj=dst)

        elif issubclass(elem_type, x.MessageType):
            fvalue = await self.message(x.get_elem(src), msg_type=elem_type, obj=dst)

        else:
            raise TypeError

        return x.set_elem(dst, fvalue) if not isinstance(fvalue, NoSetSentinel) else fvalue

    async def _dump_field(self, elem, elem_type, params=None, obj=None):
        return await self.field(elem=elem, elem_type=elem_type, params=params, obj=obj)

    async def _load_field(self, elem_type, params=None, elem=None, obj=None):
        return await self.field(elem=elem, elem_type=elem_type, params=params, obj=obj)


def container_is_raw(container_type, params):
    """
    Returns true if container is statically allocated array
    :param container_type:
    :param params:
    :return:
    """
    return container_type.KV_RAW_ARRAY if hasattr(container_type, 'KV_RAW_ARRAY') else False

