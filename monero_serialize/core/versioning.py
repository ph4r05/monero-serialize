from . import obj_helper as oh
from . import base_types as bt
from . import message_types as mt
from typing import Dict, Tuple, List, Optional, Any


class TypeWrapper(object):
    """
    Serialization type wrapper - versioning.
    Primitive types not versioned.
    """
    ELEMENTARY_RES = 0, 0

    def __init__(self, tp, params=None):
        self.tp = tp
        self.params = TypeWrapper.wrap_params(params)

    @staticmethod
    def is_elementary_type(elem_type):
        """
        Returns True if the type is elementary - not versioned
        :param elem_type:
        :return:
        """
        if not oh.is_type(elem_type, bt.XmrType):
            return False
        if oh.is_type(elem_type, (bt.UVarintType, bt.IntType, mt.UnicodeType)):
            return True
        return False

    @staticmethod
    def wrap_params(params):
        if params is None:
            return None
        if isinstance(params, (tuple, list)) and len(params) == 0:
            return None
        if not isinstance(params, (tuple, list)):
            params = (params, )
        return params

    def is_elementary(self):
        return TypeWrapper.is_elementary_type(self.tp)

    def is_versioned(self):
        if TypeWrapper.is_elementary_type(self.tp):
            return False
        if hasattr(self.tp, 'boost_versioned'):
            return self.tp.boost_versioned()
        if hasattr(self.tp, 'VERSIONED'):
            return self.VERSIONED
        else:
            return True

    def get_current_version(self, prefix=None):
        if prefix == 'bc':
            if hasattr(self.tp, 'bc_version'):
                return self.tp.bc_version()
            if hasattr(self.tp, 'BC_VERSION'):
                return self.tp.BC_VERSION

        if hasattr(self.tp, 'boost_version'):
            return self.tp.boost_version()
        if hasattr(self.tp, 'BOOST_VERSION'):
            return self.tp.BOOST_VERSION
        else:
            return 0

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.tp == other.tp and self.params == other.params

    def __hash__(self):
        return hash(self.tp) ^ hash(self.params)

    def __repr__(self):
        return 'Type<%r:%r>' % (self.tp, self.params)


class VersionDatabase(object):
    """
    Boost version database - singletons
    """
    def __init__(self):
        self.db = {}  # type: Dict[type, Tuple[int, int]]

    def is_versioned(self, twrap):
        """
        Returns true if type wrapper is versioned
        :param twrap:
        :return:
        """
        return twrap in self.db

    def get_version(self, twrap):
        return self.db[twrap]

    def set_version(self, twrap, track, version):
        if self.is_versioned(twrap):
            return False
        self.db[twrap] = (track, version)


class VersionSetting(object):
    def __init__(self, db_init=None):
        self.db = {}  # type: Dict[type, int]
        self.current_idx = 0
        self.iter_keys = None

        if db_init:
            self.set_all(db_init)

    def wrap(self, inp, params=None):
        if isinstance(inp, TypeWrapper):
            return inp
        elif isinstance(inp, tuple):
            return TypeWrapper(inp[0], params[1])
        return TypeWrapper(inp, params)

    def set_all(self, db):
        for k in db:
            self.set(k, db[k])
        return self

    def set(self, twrap, version, params=None):
        twrap = self.wrap(twrap, params)
        if twrap in self.db:
            return self
        self.db[twrap] = version
        return self

    def delete(self, twrap, params=None):
        twrap = self.wrap(twrap, params)
        del self.db[twrap]

    def __getitem__(self, item):
        item = self.wrap(item)
        return self.db[item]

    def __setitem__(self, key, value):
        key = self.wrap(key)
        self.db[key] = value

    def __len__(self):
        return len(self.db)

    def __contains__(self, item):
        return self.wrap(item) in self.db

    def __iter__(self):
        self.iter_keys = list(self.db.keys())
        self.current_idx = 0
        return self

    def __next__(self):
        if self.current_idx >= len(self.iter_keys):
            raise StopIteration
        else:
            self.current_idx += 1
            c_key = self.iter_keys[self.current_idx - 1]
            return c_key, self[c_key]
