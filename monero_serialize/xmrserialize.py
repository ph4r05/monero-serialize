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

For de-serializing (loading) types, object with `AsyncReader`
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

import logging
import sys

from . import helpers
from .protobuf import const, load_uvarint, dump_uvarint
from .core.readwriter import MemoryReaderWriter
from .core.base_types import *
from .core.erefs import has_elem, set_elem, get_elem, ElemRefArr, ElemRefObj, eref, is_elem_ref
from .core.int_serialize import *
from .core.message_types import *
from .core.obj_helper import *
from .core.versioning import TypeWrapper, VersionDatabase, VersionSetting


logger = logging.getLogger(__name__)


def import_def(module, name):
    if module not in sys.modules:
        if not module.startswith("monero_serialize"):
            raise ValueError("Module not allowed: %s" % module)

        logger.debug("Importing: from %s import %s", module, name)
        __import__(module, None, None, (name,), 0)

    r = getattr(sys.modules[module], name)
    return r


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
    def __init__(self, iobj, writing=True, versions=None, **kwargs):
        self.writing = writing
        self.iobj = iobj
        self.tracker = helpers.Tracker()

        # Using boost versioning also for BC format.
        self.version_settings = versions  # type: VersionSetting

    def _cur_version(self, tw, elem=None):
        has_version = False
        if elem:
            relem = get_elem(elem)
            if relem and hasattr(relem, 'BOOST_VERSION_CUR'):
                version = getattr(relem, 'BOOST_VERSION_CUR')
                has_version = True

        if not has_version and self.version_settings and tw in self.version_settings:
            version = self.version_settings[tw]

        else:
            version = tw.get_current_version('bc')
        return version

    async def version(self, tp, params, version=None, elem=None):
        tw = TypeWrapper(tp, params)
        return self._cur_version(tw, elem)

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

    async def uint(self, elem, elem_type, params=None, width=None):
        """
        Fixed size int
        :param elem:
        :param elem_type:
        :param params:
        :param width:
        :return:
        """
        if self.writing:
            return await dump_uint(self.iobj, elem, width if width else elem_type.WIDTH)
        else:
            return await load_uint(self.iobj, width if width else elem_type.WIDTH)

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
        if hasattr(elem_type, "serialize_archive"):
            elem = elem_type() if elem is None else elem
            return await elem.serialize_archive(
                self, elem=elem, elem_type=elem_type, params=params
            )

        if self.writing:
            return await dump_blob(
                self.iobj, elem=elem, elem_type=elem_type, params=params
            )
        else:
            return await load_blob(
                self.iobj, elem_type=elem_type, params=params, elem=elem
            )

    async def container(self, container=None, container_type=None, params=None):
        """
        Loads/dumps container
        :return:
        """
        if hasattr(container_type, "serialize_archive"):
            container = container_type() if container is None else container
            return await container.serialize_archive(
                self, elem=container, elem_type=container_type, params=params
            )

        if self.writing:
            return await self._dump_container(
                self.iobj, container, container_type, params
            )
        else:
            return await self._load_container(
                self.iobj, container_type, params=params, container=container
            )

    async def container_size(
            self, container_len=None, container_type=None, params=None
    ):
        """
        Container size
        :param container_len:
        :param container_type:
        :param params:
        :return:
        """
        if hasattr(container_type, "serialize_archive"):
            raise ValueError("not supported")

        if self.writing:
            return await self._dump_container_size(
                self.iobj, container_len, container_type, params
            )
        else:
            raise ValueError("Not supported")

    async def container_val(self, elem, container_type, params=None):
        """
        Single cont value
        :param elem:
        :param container_type:
        :param params:
        :return:
        """
        if hasattr(container_type, "serialize_archive"):
            raise ValueError("not supported")
        if self.writing:
            return await self._dump_container_val(
                self.iobj, elem, container_type, params
            )
        else:
            raise ValueError("Not supported")

    async def tuple(self, elem=None, elem_type=None, params=None):
        """
        Loads/dumps tuple
        :return:
        """
        if hasattr(elem_type, "serialize_archive"):
            container = elem_type() if elem is None else elem
            return await container.serialize_archive(
                self, elem=elem, elem_type=elem_type, params=params
            )

        if self.writing:
            return await self._dump_tuple(self.iobj, elem, elem_type, params)
        else:
            return await self._load_tuple(
                self.iobj, elem_type, params=params, elem=elem
            )

    async def variant(self, elem=None, elem_type=None, params=None, wrapped=None):
        """
        Loads/dumps variant type
        :param elem:
        :param elem_type:
        :param params:
        :return:
        """
        elem_type = elem_type if elem_type else elem.__class__
        if hasattr(elem_type, "serialize_archive"):
            elem = elem_type() if elem is None else elem
            return await elem.serialize_archive(
                self, elem=elem, elem_type=elem_type, params=params
            )

        if self.writing:
            return await self._dump_variant(
                self.iobj,
                elem=elem,
                elem_type=elem_type if elem_type else elem.__class__,
                params=params,
            )
        else:
            return await self._load_variant(
                self.iobj,
                elem_type=elem_type if elem_type else elem.__class__,
                params=params,
                elem=elem,
                wrapped=wrapped,
            )

    async def message(self, msg, msg_type=None, use_version=None):
        """
        Loads/dumps message
        Format: *fields

        :param msg:
        :param msg_type:
        :param use_version:
        :return:
        """
        elem_type = msg_type if msg_type is not None else msg.__class__
        msg = elem_type() if msg is None else msg
        if hasattr(elem_type, "serialize_archive"):
            version = await self.version(elem_type, None, elem=msg) if use_version is None else use_version
            return await msg.serialize_archive(self, version=version)

        mtype = msg.__class__ if msg_type is None else msg_type
        fields = mtype.f_specs()
        if hasattr(mtype, "serialize_archive"):
            raise ValueError("Cannot directly load, has to use archive with %s" % mtype)

        await self.message_fields(msg, fields)
        return msg

    async def message_field(self, msg, field, fvalue=None):
        """
        Dumps/Loads message field
        :param msg:
        :param field:
        :param fvalue: explicit value for dump
        :return:
        """
        fname, ftype, params = field[0], field[1], field[2:]
        try:
            self.tracker.push_field(fname)
            if self.writing:
                await self._dump_message_field(self.iobj, msg, field, fvalue=fvalue)
            else:
                await self._load_message_field(self.iobj, msg, field)
            self.tracker.pop()

        except Exception as e:
            raise helpers.ArchiveException(e, tracker=self.tracker) from e

    async def message_fields(self, msg, fields):
        """
        Load/dump individual message fields
        :param msg:
        :param fields:
        :return:
        """
        for field in fields:
            await self.message_field(msg, field)
        return msg

    def _get_type(self, elem_type):
        # If part of our hierarchy - return the object
        if issubclass(elem_type, XmrType):
            return elem_type

        # Basic decision types
        etypes = (
            UVarintType,
            IntType,
            BlobType,
            UnicodeType,
            VariantType,
            ContainerType,
            TupleType,
            MessageType,
        )
        cname = elem_type.__name__
        for e in etypes:
            if cname == e.__name__:
                return e

        # Inferred type: need to translate it to the current
        try:
            m = elem_type.__module__
            r = import_def(m, cname)
            sub_test = issubclass(r, XmrType)
            logger.debug(
                "resolved %s, sub: %s, id_e: %s, id_mod: %s",
                r,
                sub_test,
                id(r),
                id(sys.modules[m]),
            )
            if not sub_test:
                logger.warning("resolution hierarchy broken")

            return r

        except Exception as e:
            raise ValueError(
                "Could not translate elem type: %s %s, exc: %s %s"
                % (type(elem_type), elem_type, type(e), e)
            )

    def _is_type(self, elem_type, test_type):
        return issubclass(elem_type, test_type)

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

        etype = self._get_type(elem_type)
        if self._is_type(etype, UVarintType):
            fvalue = await self.uvarint(get_elem(elem))

        elif self._is_type(etype, IntType):
            fvalue = await self.uint(
                elem=get_elem(elem), elem_type=elem_type, params=params
            )

        elif self._is_type(etype, BlobType):
            fvalue = await self.blob(
                elem=get_elem(elem), elem_type=elem_type, params=params
            )

        elif self._is_type(etype, UnicodeType):
            fvalue = await self.unicode_type(get_elem(elem))

        elif self._is_type(etype, VariantType):
            fvalue = await self.variant(
                elem=get_elem(elem), elem_type=elem_type, params=params
            )

        elif self._is_type(etype, ContainerType):  # container ~ simple list
            fvalue = await self.container(
                container=get_elem(elem), container_type=elem_type, params=params
            )

        elif self._is_type(etype, TupleType):  # tuple ~ simple list
            fvalue = await self.tuple(
                elem=get_elem(elem), elem_type=elem_type, params=params
            )

        elif self._is_type(etype, MessageType):
            fvalue = await self.message(get_elem(elem), msg_type=elem_type)

        else:
            raise TypeError(
                "unknown type: %s %s %s" % (elem_type, type(elem_type), elem)
            )

        return fvalue if self.writing else set_elem(elem, fvalue)

    async def dump_field(self, writer, elem, elem_type, params=None):
        assert self.iobj == writer
        return await self.field(elem=elem, elem_type=elem_type, params=params)

    async def load_field(self, reader, elem_type, params=None, elem=None):
        assert self.iobj == reader
        return await self.field(elem=elem, elem_type=elem_type, params=params)

    async def root(self):
        """
        Root level archive init
        :return:
        """

    async def _dump_container_size(
            self, writer, container_len, container_type, params=None
    ):
        """
        Dumps container size - per element streaming
        :param writer:
        :param container_len:
        :param container_type:
        :param params:
        :return:
        """
        if not container_type or not container_type.FIX_SIZE:
            await dump_uvarint(writer, container_len)
        elif container_len != container_type.SIZE:
            raise ValueError(
                "Fixed size container has not defined size: %s" % container_type.SIZE
            )

    async def _dump_container_val(self, writer, elem, container_type, params=None):
        """
        Single elem dump
        :param writer:
        :param elem:
        :param container_type:
        :param params:
        :return:
        """
        elem_type = container_elem_type(container_type, params)
        await self.dump_field(writer, elem, elem_type, params[1:] if params else None)

    async def _dump_container(self, writer, container, container_type, params=None):
        """
        Dumps container of elements to the writer.
        Format:
            - `uvarint(len) || *elements` for containers of unknown size
            - `*elements` for containers of a fixed size

        :param writer:
        :param container:
        :param container_type:
        :param params:
        :return:
        """
        await self._dump_container_size(writer, len(container), container_type)

        elem_type = container_elem_type(container_type, params)

        for idx, elem in enumerate(container):
            try:
                self.tracker.push_index(idx)
                await self.dump_field(
                    writer, elem, elem_type, params[1:] if params else None
                )
                self.tracker.pop()
            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

    async def _load_container(
            self, reader, container_type, params=None, container=None
    ):
        """
        Loads container of elements from the reader. Supports the container ref.
        Returns loaded container.

        :param reader:
        :param container_type:
        :param params:
        :param container:
        :return:
        """

        c_len = (
            container_type.SIZE
            if container_type.FIX_SIZE
            else await load_uvarint(reader)
        )
        if container and get_elem(container) and c_len != len(container):
            raise ValueError("Size mismatch")

        elem_type = container_elem_type(container_type, params)
        res = container if container else []
        for i in range(c_len):
            try:
                self.tracker.push_index(i)
                fvalue = await self.load_field(
                    reader,
                    elem_type,
                    params[1:] if params else None,
                    eref(res, i) if container else None,
                )
                self.tracker.pop()
            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

            if not container:
                res.append(fvalue)
        return res

    async def _dump_tuple(self, writer, elem, elem_type, params=None):
        """
        Dumps tuple of elements to the writer.
        Format: `uvarint(len) || *elements`

        :param writer:
        :param elem:
        :param elem_type:
        :param params:
        :return:
        """
        if len(elem) != len(elem_type.f_specs()):
            raise ValueError(
                "Fixed size tuple has not defined size: %s" % len(elem_type.f_specs())
            )
        await dump_uvarint(writer, len(elem))

        elem_fields = params[0] if params else None
        if elem_fields is None:
            elem_fields = elem_type.f_specs()
        for idx, elem in enumerate(elem):
            try:
                self.tracker.push_index(idx)
                await self.dump_field(
                    writer, elem, elem_fields[idx], params[1:] if params else None
                )
                self.tracker.pop()
            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

    async def _load_tuple(self, reader, elem_type, params=None, elem=None):
        """
        Loads tuple of elements from the reader. Supports the tuple ref.
        Returns loaded tuple.

        :param reader:
        :param elem_type:
        :param params:
        :param container:
        :return:
        """

        c_len = await load_uvarint(reader)
        if elem and c_len != len(elem):
            raise ValueError("Size mismatch")
        if c_len != len(elem_type.f_specs()):
            raise ValueError("Tuple size mismatch")

        elem_fields = params[0] if params else None
        if elem_fields is None:
            elem_fields = elem_type.f_specs()

        res = elem if elem else []
        for i in range(c_len):
            try:
                self.tracker.push_index(i)
                fvalue = await self.load_field(
                    reader,
                    elem_fields[i],
                    params[1:] if params else None,
                    eref(res, i) if elem else None,
                )
                self.tracker.pop()
            except Exception as e:
                raise helpers.ArchiveException(e, tracker=self.tracker) from e

            if not elem:
                res.append(fvalue)
        return res

    async def _dump_message_field(self, writer, msg, field, fvalue=None):
        """
        Dumps a message field to the writer. Field is defined by the message field specification.

        :param writer:
        :param msg:
        :param field:
        :param fvalue:
        :return:
        """
        fname, ftype, params = field[0], field[1], field[2:]
        fvalue = getattr(msg, fname, None) if fvalue is None else fvalue
        await self.dump_field(writer, fvalue, ftype, params)

    async def _load_message_field(self, reader, msg, field):
        """
        Loads message field from the reader. Field is defined by the message field specification.
        Returns loaded value, supports field reference.

        :param reader:
        :param msg:
        :param field:
        :return:
        """
        fname, ftype, params = field[0], field[1], field[2:]
        await self.load_field(reader, ftype, params, eref(msg, fname))

    async def _dump_variant(self, writer, elem, elem_type=None, params=None):
        """
        Dumps variant type to the writer.
        Supports both wrapped and raw variant.

        Format: `variant-code-1B || field`

        :param writer:
        :param elem:
        :param elem_type:
        :param params:
        :return:
        """
        if isinstance(elem, VariantType) or elem_type.WRAPS_VALUE:
            await dump_uint(writer, elem.variant_elem_type.VARIANT_CODE, 1)
            await self.dump_field(
                writer, getattr(elem, elem.variant_elem), elem.variant_elem_type
            )

        else:
            fdef = find_variant_fdef(elem_type, elem)
            await dump_uint(writer, fdef[1].VARIANT_CODE, 1)
            await self.dump_field(writer, elem, fdef[1])

    async def _load_variant(
            self, reader, elem_type, params=None, elem=None, wrapped=None
    ):
        """
        Loads variant type from the reader.
        Supports both wrapped and raw variant.

        :param reader:
        :param elem_type:
        :param params:
        :param elem:
        :param wrapped:
        :return:
        """
        is_wrapped = (
            (isinstance(elem, VariantType) or elem_type.WRAPS_VALUE)
            if wrapped is None
            else wrapped
        )
        if is_wrapped:
            elem = elem_type() if elem is None else elem

        tag = await load_uint(reader, 1)
        for field in elem_type.f_specs():
            ftype = field[1]
            if ftype.VARIANT_CODE == tag:
                fvalue = await self.load_field(
                    reader, ftype, field[2:], elem if not is_wrapped else None
                )
                if is_wrapped:
                    elem.set_variant(field[0], fvalue)
                return elem if is_wrapped else fvalue
        raise ValueError("Unknown tag: %s" % tag)


async def dump_blob(writer, elem, elem_type, params=None):
    """
    Dumps blob message to the writer.
    Supports both blob and raw value.

    Format:
      - `uvarint(len) || data` for data with unknown size
      - `data` for data with a fixed size

    :param writer:
    :param elem:
    :param elem_type:
    :param params:
    :return:
    """
    elem_is_blob = isinstance(elem, BlobType)
    elem_params = elem if elem_is_blob or elem_type is None else elem_type
    data = bytes(getattr(elem, BlobType.DATA_ATTR) if elem_is_blob else elem)

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
    nread = await reader.areadinto(fvalue)
    if nread != ivalue:
        raise ValueError('Invalid buffer size read, nread: %s vs expecting: %s' % (nread, ivalue))

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
    Format: `uvarint(len) || input.encode('utf8')

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


def find_variant_fdef(elem_type, elem):
    fields = elem_type.f_specs()
    for x in fields:
        if isinstance(elem, x[1]):
            return x

    # Not direct hierarchy
    name = elem.__class__.__name__
    for x in fields:
        if name == x[1].__name__:
            return x

    raise ValueError("Unrecognized variant: %s" % elem)
