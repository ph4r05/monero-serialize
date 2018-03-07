#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Minimal streaming codec for a Monero binary serialization.
Used for a binary serialization in blockchain and for hash computation for signatures.

Equivalent of BEGIN_SERIALIZE_OBJECT(), /src/serialization/serialization.h

- The wire binary format does not use tags. Structure has to be read from the binary stream
with the scheme specified in order to parse the structure.

- Heavily uses variable integer serialization - similar to the UTF8 or LZ4 number encoding.

- Supports: blob, string, integer types - variable or fixed size, containers of elements,
            variant types, messages of elements

For de-sererializing (loading) types, object with `AsyncReader`
interface is required:

>>> class AsyncReader:
>>>     async def areadinto(self, buffer):
>>>         """
>>>         Reads `len(buffer)` bytes into `buffer`, or raises `EOFError`.
>>>         """

For serializing (dumping) types, object with `AsyncWriter` interface is
required:

>>> class AsyncWriter:
>>>     async def awrite(self, buffer):
>>>         """
>>>         Writes all bytes from `buffer`, or raises `EOFError`.
>>>         """
'''

from .protobuf import const, load_uvarint, dump_uvarint


_UINT_BUFFER = bytearray(1)


async def load_uint(reader, width):
    """
    Constant-width integer serialization
    :param reader:
    :param width:
    :return:
    """
    buffer = _UINT_BUFFER
    result = 0
    shift = 0
    for _ in range(width):
        await reader.areadinto(buffer)
        result += buffer[0] << shift
        shift += 8
    return result


async def dump_uint(writer, n, width):
    """
    Constant-width integer serialization
    :param writer:
    :param n:
    :param width:
    :return:
    """
    buffer = _UINT_BUFFER
    for _ in range(width):
        buffer[0] = n & 0xff
        await writer.awrite(buffer)
        n >>= 8


def eq_obj_slots(l, r):
    """
    Compares objects with __slots__ defined
    :param l:
    :param r:
    :return:
    """
    for f in l.__slots__:
        if getattr(l, f, None) != getattr(r, f, None):
            return False
    return True


def eq_obj_contents(l, r):
    """
    Compares object contents, supports slots
    :param l:
    :param r:
    :return:
    """
    if l.__class__ is not r.__class__:
        return False
    if hasattr(l, '__slots__'):
        return eq_obj_slots(l, r)
    else:
        return l.__dict__ == r.__dict__


def slot_obj_dict(o):
    """
    Builds dict for o with __slots__ defined
    :param o:
    :return:
    """
    d = {}
    for f in o.__slots__:
        d[f] = getattr(o, f, None)
    return d


class XmrType:
    VERSION = 0


class UVarintType(XmrType):
    pass


class IntType(XmrType):
    WIDTH = 0
    SIGNED = 0
    VARIABLE = 0

    def __repr__(self):
        return '%s:<w: %s, sig: %s, var: %s>' % (self.__class__, self.WIDTH, self.SIGNED, self.VARIABLE)


class BoolType(IntType):
    WIDTH = 1


class UInt8(IntType):
    WIDTH = 1


class Int8(IntType):
    SIGNED = 1
    WIDTH = 1


class UInt16(IntType):
    WIDTH = 2


class Int16(IntType):
    SIGNED = 1
    WIDTH = 2


class UInt32(IntType):
    WIDTH = 4


class Int32(IntType):
    SIGNED = 1
    WIDTH = 4


class UInt64(IntType):
    WIDTH = 8


class SizeT(UInt64):
    WIDTH = 8


class Int64(IntType):
    SIGNED = 1
    WIDTH = 8


class BlobType(XmrType):
    """
    Binary data

    Represented as bytearray() or a list of values in data structures.
    Not wrapped in the BlobType, the BlobType is only a scheme descriptor.
    Behaves in the same way as primitive types

    Supports also the wrapped version (__init__, DATA_ATTR, eq, repr...),
    """
    DATA_ATTR = 'data'
    FIX_SIZE = 0
    SIZE = 0

    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            raise ValueError()
        if len(args) > 0:
            setattr(self, self.DATA_ATTR, args[0])
        if 'SIZE' in kwargs:
            self.SIZE = kwargs['SIZE']
        if 'FIX_SIZE' in kwargs:
            self.FIX_SIZE = kwargs['FIX_SIZE']

    def __eq__(self, rhs):
        return eq_obj_contents(self, rhs)

    def __repr__(self):
        dct = slot_obj_dict(self) if hasattr(self, '__slots__') else self.__dict__
        return '<%s: %s>' % (self.__class__.__name__, dct)


class UnicodeType(XmrType):
    pass


class VariantType(XmrType):
    """
    Union of types, variant tags needed. is only one of the types. List in typedef, enum.
    Wraps the variant type in order to unambiguously support variant of variants.
    Supports also unwrapped value using type system to distinguish variants - simplifies the construction.
    """
    WRAPS_VALUE = False
    FIELDS = []

    def __init__(self, *args, **kwargs):
        self.variant_elem = None
        self.variant_elem_type = None

        fname, fval = None, None
        if len(args) > 0:
            fname, fval = self.find_fdef(self.FIELDS, args[0])[0], args[0]
        if len(kwargs) > 0:
            key = list(kwargs.keys())[0]
            fname, fval = key, kwargs[key]
        if fname:
            self.set_variant(fname, fval)

    @staticmethod
    def find_fdef(fields, elem):
        for x in fields:
            if isinstance(elem, x[1]):
                return x
        raise ValueError('Unrecognized variant')

    def set_variant(self, fname, fvalue):
        self.variant_elem = fname
        self.variant_elem_type = fvalue.__class__
        setattr(self, fname, fvalue)

    def __eq__(self, rhs):
        return eq_obj_contents(self, rhs)

    def __repr__(self):
        dct = slot_obj_dict(self) if hasattr(self, '__slots__') else self.__dict__
        return '<%s: %s>' % (self.__class__.__name__, dct)


class ContainerType(XmrType):
    """
    Array of elements
    Represented as a real array in the data structures, not wrapped in the ContainerType.
    The Container type is used only as a schema descriptor for serialization.
    """
    FIX_SIZE = 0
    SIZE = 0
    ELEM_TYPE = None

    def __init__(self, *args, **kwargs):
        if 'SIZE' in kwargs:
            self.SIZE = kwargs['SIZE']
        if 'FIX_SIZE' in kwargs:
            self.FIX_SIZE = kwargs['FIX_SIZE']
        if 'ELEM_TYPE' in kwargs:
            self.ELEM_TYPE = kwargs['ELEM_TYPE']


class TupleType(XmrType):
    FIELDS = []  # simple types without file name

    def __init__(self, *args, **kwargs):
        if 'FIELDS' in kwargs:
            self.FIELDS = kwargs['FIELDS']


class MessageType(XmrType):
    FIELDS = {}

    def __init__(self, **kwargs):
        for kw in kwargs:
            setattr(self, kw, kwargs[kw])

    def __eq__(self, rhs):
        return eq_obj_contents(self, rhs)

    def __repr__(self):
        dct = slot_obj_dict(self) if hasattr(self, '__slots__') else self.__dict__
        return '<%s: %s>' % (self.__class__.__name__, dct)


FLAG_REPEATED = const(1)


class MemoryReaderWriter:

    def __init__(self, buffer=None):
        self.buffer = buffer if buffer else []
        self.nread = 0
        self.nwritten = 0

    async def areadinto(self, buf):
        ln = len(buf)
        nread = min(ln, len(self.buffer))
        for idx in range(nread):
            buf[idx] = self.buffer.pop(0)
        self.nread += nread
        return nread

    async def awrite(self, buf):
        self.buffer.extend(buf)
        nwritten = len(buf)
        self.nwritten += nwritten
        return nwritten


class ElemRefObj:
    def __repr__(self):
        return 'RefObj'


class ElemRefArr:
    def __repr__(self):
        return 'RefAssoc'


def gen_elem_array(size, elem_type=None):
    """
    Generates element array of given size and initializes with given type.
    Supports container type, used for pre-allocation before deserialization.
    :param size:
    :param elem_type:
    :return:
    """
    if elem_type is None or not callable(elem_type):
        return [elem_type] * size
    if isinstance(elem_type, ContainerType) or issubclass(elem_type, ContainerType):
        elem_type = lambda: []
    res = []
    for _ in range(size):
        res.append(elem_type())
    return res


def is_elem_ref(elem_ref):
    """
    Returns true if the elem_ref is an element reference

    :param elem_ref:
    :return:
    """
    return elem_ref and isinstance(elem_ref, tuple) and len(elem_ref) == 3 \
           and (elem_ref[0] == ElemRefObj or elem_ref[0] == ElemRefArr)


def get_elem(elem_ref, default=None):
    """
    Gets the element referenced by elem_ref or returns the elem_ref directly if its not a reference.

    :param elem_ref:
    :param default:
    :return:
    """
    if not is_elem_ref(elem_ref):
        return elem_ref
    elif elem_ref[0] == ElemRefObj:
        return getattr(elem_ref[1], elem_ref[2], default)
    elif elem_ref[0] == ElemRefArr:
        return elem_ref[1][elem_ref[2]]


def set_elem(elem_ref, elem):
    """
    Sets element referenced by the elem_ref. Returns the elem.

    :param elem_ref:
    :param elem:
    :return:
    """
    if elem_ref is None or elem_ref == elem or not is_elem_ref(elem_ref):
        return elem

    elif elem_ref[0] == ElemRefObj:
        setattr(elem_ref[1], elem_ref[2], elem)
        return elem

    elif elem_ref[0] == ElemRefArr:
        elem_ref[1][elem_ref[2]] = elem
        return elem


def eref(obj, key, is_assoc=None):
    """
    Returns element reference
    :param obj:
    :param key:
    :param is_assoc:
    :return:
    """
    if obj is None:
        return None
    if isinstance(key, int) or (is_assoc is not None and is_assoc):
        return ElemRefArr, get_elem(obj), key
    else:
        return ElemRefObj, get_elem(obj), key


class Archive(object):
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
        self.writing = writing
        self.iobj = iobj

    async def tag(self, tag):
        """

        :param tag:
        :return:
        """

    async def begin_array(self):
        """
        Mark start of the array. Used for JSON serialization.
        :return:
        """

    async def end_array(self):
        """
        Mark end of the array. Used for JSON serialization.
        :return:
        """

    async def begin_object(self):
        """
        Mark start of the object. Used for JSON serialization.
        :return:
        """

    async def end_object(self):
        """
        Mark end of the object. Used for JSON serialization.
        :return:
        """

    async def prepare_container(self, size, container, elem_type=None):
        """
        Prepares container for serialization
        :param size:
        :param container:
        :return:
        """
        if not self.writing:
            if container is None:
                return gen_elem_array(size, elem_type)

            fvalue = get_elem(container)
            if fvalue is None:
                fvalue = []
            fvalue += gen_elem_array(max(0, size - len(fvalue)), elem_type)
            set_elem(container, fvalue)
            return fvalue

    async def prepare_message(self, msg, msg_type):
        """
        Prepares message for serialization
        :param msg:
        :param msg_type:
        :return:
        """
        if self.writing:
            return
        return set_elem(msg, msg_type())

    async def uvarint(self, elem):
        """
        Uvarint
        :param elem:
        :return:
        """
        if self.writing:
            return await dump_uvarint(self.iobj, elem)
        else:
            return await load_uvarint(self.iobj)

    async def uint(self, elem, elem_type, params=None):
        """
        Fixed size int
        :param elem:
        :param elem_type:
        :param params:
        :return:
        """
        if self.writing:
            return await dump_uint(self.iobj, elem, elem_type.WIDTH)
        else:
            return await load_uint(self.iobj, elem_type.WIDTH)

    async def unicode_type(self, elem):
        """
        Unicode type
        :param elem:
        :return:
        """
        if self.writing:
            return await dump_unicode(self.iobj, elem)
        else:
            return await load_unicode(self.iobj)

    async def blob(self, elem=None, elem_type=None, params=None):
        """
        Loads/dumps blob
        :return:
        """
        elem_type = elem_type if elem_type else elem.__class__
        if hasattr(elem_type, 'serialize_archive'):
            elem = elem_type() if elem is None else elem
            return await elem.serialize_archive(self, elem=elem, elem_type=elem_type, params=params)

        if self.writing:
            return await dump_blob(self.iobj, elem=elem, elem_type=elem_type, params=params)
        else:
            return await load_blob(self.iobj, elem_type=elem_type, params=params, elem=elem)

    async def container(self, container=None, container_type=None, params=None):
        """
        Loads/dumps container
        :return:
        """
        if hasattr(container_type, 'serialize_archive'):
            container = container_type() if container is None else container
            return await container.serialize_archive(self, elem=container, elem_type=container_type, params=params)

        if self.writing:
            return await dump_container(self.iobj, container, container_type, params,
                                        field_archiver=self.dump_field)
        else:
            return await load_container(self.iobj, container_type, params=params, container=container,
                                        field_archiver=self.load_field)

    async def tuple(self, elem=None, elem_type=None, params=None):
        """
        Loads/dumps tuple
        :return:
        """
        if hasattr(elem_type, 'serialize_archive'):
            container = elem_type() if elem is None else elem
            return await container.serialize_archive(self, elem=elem, elem_type=elem_type, params=params)

        if self.writing:
            return await dump_tuple(self.iobj, elem, elem_type, params,
                                    field_archiver=self.dump_field)
        else:
            return await load_tuple(self.iobj, elem_type, params=params, elem=elem,
                                    field_archiver=self.load_field)

    async def variant(self, elem=None, elem_type=None, params=None):
        """
        Loads/dumps variant type
        :param elem:
        :param elem_type:
        :param params:
        :return:
        """
        elem_type = elem_type if elem_type else elem.__class__
        if hasattr(elem_type, 'serialize_archive'):
            elem = elem_type() if elem is None else elem
            return await elem.serialize_archive(self, elem=elem, elem_type=elem_type, params=params)

        if self.writing:
            return await dump_variant(self.iobj, elem=elem,
                                      elem_type=elem_type if elem_type else elem.__class__,
                                      params=params, field_archiver=self.dump_field)
        else:
            return await load_variant(self.iobj, elem_type=elem_type if elem_type else elem.__class__,
                                      params=params, elem=elem, field_archiver=self.load_field)

    async def message(self, msg, msg_type=None):
        """
        Loads/dumps message
        :param msg:
        :param msg_type:
        :return:
        """
        elem_type = msg_type if msg_type is not None else msg.__class__
        if hasattr(elem_type, 'serialize_archive'):
            msg = elem_type() if msg is None else msg
            return await msg.serialize_archive(self)

        if self.writing:
            return await dump_message(self.iobj, msg, msg_type=msg_type, field_archiver=self.dump_field)
        else:
            return await load_message(self.iobj, msg_type, msg=msg, field_archiver=self.load_field)

    async def message_field(self, msg, field):
        """
        Dumps/Loads message field
        :param msg:
        :param field:
        :return:
        """
        if self.writing:
            await dump_message_field(self.iobj, msg, field, field_archiver=self.dump_field)
        else:
            await load_message_field(self.iobj, msg, field, field_archiver=self.load_field)

    async def msg_fields(self, msg, fields):
        """
        Load/dump individual message fields
        :param msg:
        :param fields:
        :param field_archiver:
        :return:
        """
        for field in fields:
            await self.message_field(msg, field)
        return msg

    async def rfield(self, elem=None, elem_type=None, params=None):
        """
        Loads/Dumps message field
        :param elem:
        :param elem_type:
        :param params:
        :return:
        """
        if self.writing:
            return await dump_field(self.iobj, elem=elem,
                                    elem_type=elem_type if elem_type else elem.__class__,
                                    params=params)
        else:
            return await load_field(self.iobj,
                                    elem_type=elem_type if elem_type else elem.__class__,
                                    params=params,
                                    elem=elem)

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
        if issubclass(elem_type, UVarintType):
            fvalue = await self.uvarint(get_elem(elem))

        elif issubclass(elem_type, IntType):
            fvalue = await self.uint(elem=get_elem(elem), elem_type=elem_type, params=params)

        elif issubclass(elem_type, BlobType):
            fvalue = await self.blob(elem=get_elem(elem), elem_type=elem_type, params=params)

        elif issubclass(elem_type, UnicodeType):
            fvalue = await self.unicode_type(get_elem(elem))

        elif issubclass(elem_type, VariantType):
            fvalue = await self.variant(elem=get_elem(elem), elem_type=elem_type, params=params)

        elif issubclass(elem_type, ContainerType):  # container ~ simple list
            fvalue = await self.container(container=get_elem(elem), container_type=elem_type, params=params)

        elif issubclass(elem_type, TupleType):  # tuple ~ simple list
            fvalue = await self.tuple(elem=get_elem(elem), elem_type=elem_type, params=params)

        elif issubclass(elem_type, MessageType):
            fvalue = await self.message(get_elem(elem), msg_type=elem_type)

        else:
            raise TypeError

        return fvalue if self.writing else set_elem(elem, fvalue)

    async def dump_field(self, writer, elem, elem_type, params=None):
        assert self.iobj == writer
        return await self.field(elem=elem, elem_type=elem_type, params=params)

    async def load_field(self, reader, elem_type, params=None, elem=None):
        assert self.iobj == reader
        return await self.field(elem=elem, elem_type=elem_type, params=params)


async def dump_blob(writer, elem, elem_type, params=None):
    """
    Dumps blob message to the writer.
    Supports both blob and raw value.

    :param writer:
    :param elem:
    :param elem_type:
    :param params:
    :return:
    """
    elem_is_blob = isinstance(elem, BlobType)
    elem_params = elem if elem_is_blob or elem_type is None else elem_type
    data = getattr(elem, BlobType.DATA_ATTR) if elem_is_blob else elem

    if not elem_params.FIX_SIZE:
        await dump_uvarint(writer, len(elem))
    elif len(data) != elem_params.SIZE:
        raise ValueError('Fixed size blob has not defined size: %s' % elem_params.SIZE)
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
    ivalue = elem_type.SIZE if elem_type.FIX_SIZE else await load_uvarint(reader)
    fvalue = bytearray(ivalue)
    await reader.areadinto(fvalue)

    if elem is None:
        return fvalue  # array by default

    elif isinstance(elem, BlobType):
        setattr(elem, elem_type.DATA_ATTR, fvalue)
        return elem

    else:
        elem.extend(fvalue)

    return elem


async def dump_unicode(writer, elem):
    """
    Dumps string as UTF8 encoded string
    :param writer:
    :param elem:
    :return:
    """
    await dump_uvarint(writer, len(elem))
    await writer.awrite(bytes(elem, 'utf8'))


async def load_unicode(reader):
    """
    Loads UTF8 string
    :param reader:
    :return:
    """
    ivalue = await load_uvarint(reader)
    fvalue = bytearray(ivalue)
    await reader.areadinto(fvalue)
    return str(fvalue, 'utf8')


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
    if not container_type.FIX_SIZE:
        await dump_uvarint(writer, len(container))
    elif len(container) != container_type.SIZE:
        raise ValueError('Fixed size container has not defined size: %s' % container_type.SIZE)

    field_archiver = field_archiver if field_archiver else dump_field
    elem_type = params[0] if params else None
    if elem_type is None:
        elem_type = container_type.ELEM_TYPE
    for elem in container:
        await field_archiver(writer, elem, elem_type, params[1:] if params else None)


async def load_container(reader, container_type, params=None, container=None, field_archiver=None):
    """
    Loads container of elements from the reader. Supports the container ref.
    Returns loaded container.

    :param reader:
    :param container_type:
    :param params:
    :param container:
    :param field_archiver:
    :return:
    """
    field_archiver = field_archiver if field_archiver else load_field

    c_len = container_type.SIZE if container_type.FIX_SIZE else await load_uvarint(reader)
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


async def dump_tuple(writer, elem, elem_type, params=None, field_archiver=None):
    """
    Dumps tuple of elements to the writer.

    :param writer:
    :param elem:
    :param elem_type:
    :param params:
    :param field_archiver:
    :return:
    """
    if len(elem) != len(elem_type.FIELDS):
        raise ValueError('Fixed size tuple has not defined size: %s' % len(elem_type.FIELDS))
    await dump_uvarint(writer, len(elem))

    field_archiver = field_archiver if field_archiver else dump_field
    elem_fields = params[0] if params else None
    if elem_fields is None:
        elem_fields = elem_type.FIELDS
    for idx, elem in enumerate(elem):
        await field_archiver(writer, elem, elem_fields[idx], params[1:] if params else None)


async def load_tuple(reader, elem_type, params=None, elem=None, field_archiver=None):
    """
    Loads tuple of elements from the reader. Supports the tuple ref.
    Returns loaded tuple.

    :param reader:
    :param elem_type:
    :param params:
    :param container:
    :param field_archiver:
    :return:
    """
    field_archiver = field_archiver if field_archiver else load_field

    c_len = await load_uvarint(reader)
    if elem and c_len != len(elem):
        raise ValueError('Size mismatch')
    if c_len != len(elem_type.FIELDS):
        raise ValueError('Tuple size mismatch')

    elem_fields = params[0] if params else None
    if elem_fields is None:
        elem_fields = elem_type.FIELDS

    res = elem if elem else []
    for i in range(c_len):
        fvalue = await field_archiver(reader, elem_fields[i],
                                      params[1:] if params else None,
                                      eref(res, i) if elem else None)
        if not elem:
            res.append(fvalue)
    return res


async def dump_message_field(writer, msg, field, field_archiver=None):
    """
    Dumps a message field to the writer. Field is defined by the message field specification.

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


async def dump_message(writer, msg, msg_type=None, field_archiver=None):
    """
    Dumps message to the writer.

    :param writer:
    :param msg:
    :param msg_type:
    :param field_archiver:
    :return:
    """
    mtype = msg.__class__ if msg_type is None else msg_type
    fields = mtype.FIELDS
    if hasattr(mtype, 'serialize_archive'):
        raise ValueError('Cannot directly load, has to use archive with %s' % mtype)

    for field in fields:
        await dump_message_field(writer, msg=msg, field=field, field_archiver=field_archiver)


async def load_message(reader, msg_type, msg=None, field_archiver=None):
    """
    Loads message if the given type from the reader.
    Supports reading directly to existing message.

    :param reader:
    :param msg_type:
    :param msg:
    :param field_archiver:
    :return:
    """
    msg = msg_type() if msg is None else msg
    fields = msg_type.FIELDS if msg_type else msg.__class__.FIELDS
    if hasattr(msg_type, 'serialize_archive'):
        raise ValueError('Cannot directly load, has to use archive with %s' % msg_type)

    for field in fields:
        await load_message_field(reader, msg, field, field_archiver=field_archiver)

    return msg


async def dump_variant(writer, elem, elem_type=None, params=None, field_archiver=None):
    """
    Dumps variant type to the writer.
    Supports both wrapped and raw variant.

    :param writer:
    :param elem:
    :param elem_type:
    :param params:
    :param field_archiver:
    :return:
    """
    field_archiver = field_archiver if field_archiver else dump_field
    if isinstance(elem, VariantType) or elem_type.WRAPS_VALUE:
        await dump_uint(writer, elem.variant_elem_type.VARIANT_CODE, 1)
        await field_archiver(writer, getattr(elem, elem.variant_elem), elem.variant_elem_type)

    else:
        fdef = elem_type.find_fdef(elem_type.FIELDS, elem)
        await dump_uint(writer, fdef[1].VARIANT_CODE, 1)
        await field_archiver(writer, elem, fdef[1])


async def load_variant(reader, elem_type, params=None, elem=None, wrapped=None, field_archiver=None):
    """
    Loads variant type from the reader.
    Supports both wrapped and raw variant.

    :param reader:
    :param elem_type:
    :param params:
    :param elem:
    :param wrapped:
    :param field_archiver:
    :return:
    """
    is_wrapped = (isinstance(elem, VariantType) or elem_type.WRAPS_VALUE) if wrapped is None else wrapped
    if is_wrapped:
        elem = elem_type() if elem is None else elem

    field_archiver = field_archiver if field_archiver else load_field
    tag = await load_uint(reader, 1)
    for field in elem_type.FIELDS:
        ftype = field[1]
        if ftype.VARIANT_CODE == tag:
            fvalue = await field_archiver(reader, ftype, field[2:], elem if not is_wrapped else None)
            if is_wrapped:
                elem.set_variant(field[0], fvalue)
            return elem if is_wrapped else fvalue
    raise ValueError('Unknown tag: %s' % tag)


async def dump_field(writer, elem, elem_type, params=None):
    """
    Dumps field to the writer, according to the element specification.
    General multiplexer.

    :param writer:
    :param elem:
    :param elem_type:
    :param params:
    :return:
    """
    if issubclass(elem_type, UVarintType):
        await dump_uvarint(writer, elem)

    elif issubclass(elem_type, IntType):
        await dump_uint(writer, elem, elem_type.WIDTH)

    elif issubclass(elem_type, BlobType):
        await dump_blob(writer, elem, elem_type, params)

    elif issubclass(elem_type, UnicodeType):
        await dump_unicode(elem)

    elif issubclass(elem_type, VariantType):
        await dump_variant(writer, elem, elem_type, params)

    elif issubclass(elem_type, ContainerType):  # container ~ simple list
        await dump_container(writer, elem, elem_type, params)

    elif issubclass(elem_type, TupleType):  # container ~ simple list
        await dump_tuple(writer, elem, elem_type, params)

    elif issubclass(elem_type, MessageType):
        await dump_message(writer, elem, elem_type)

    else:
        raise TypeError


async def load_field(reader, elem_type, params=None, elem=None):
    """
    Loads a field from the reader, based on the field type specification. Demultiplexer.

    :param reader:
    :param elem_type:
    :param params:
    :param elem:
    :return:
    """
    if issubclass(elem_type, UVarintType):
        fvalue = await load_uvarint(reader)
        return set_elem(elem, fvalue)

    elif issubclass(elem_type, BoolType):
        fvalue = await load_uint(reader, elem_type.WIDTH)
        if fvalue != 0 and fvalue != 1:
            raise ValueError('Unexpected bool value')
        return set_elem(elem, fvalue)

    elif issubclass(elem_type, IntType):
        fvalue = await load_uint(reader, elem_type.WIDTH)
        return set_elem(elem, fvalue)

    elif issubclass(elem_type, BlobType):
        fvalue = await load_blob(reader, elem_type, params=params, elem=get_elem(elem))
        return set_elem(elem, fvalue)

    elif issubclass(elem_type, UnicodeType):
        fvalue = await load_unicode(reader)
        return set_elem(elem, fvalue)

    elif issubclass(elem_type, VariantType):
        fvalue = await load_variant(reader, elem_type, params=params, elem=get_elem(elem))
        return set_elem(elem, fvalue)

    elif issubclass(elem_type, ContainerType):  # container ~ simple list
        fvalue = await load_container(reader, elem_type, params=params, container=get_elem(elem))
        return set_elem(elem, fvalue)

    elif issubclass(elem_type, TupleType):  # tuple ~ simple list
        fvalue = await load_tuple(reader, elem_type, params=params, elem=get_elem(elem))
        return set_elem(elem, fvalue)

    elif issubclass(elem_type, MessageType):
        fvalue = await load_message(reader, msg_type=elem_type, msg=get_elem(elem))
        return set_elem(elem, fvalue)

    else:
        raise TypeError


