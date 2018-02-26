#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
XMR types
'''


from .protobuf import const, load_uvarint, dump_uvarint, LimitedReader, CountingWriter
from . import xmrserialize as x


#
# cryptonote_basic.h
#


class ECKey(x.BlobType):
    __slots__ = ['bytes']
    DATA_ATTR = 'bytes'
    FIX_SIZE = 1
    SIZE = 32


class ECPoint(x.BlobType):
    __slots__ = ['data']
    DATA_ATTR = 'data'
    FIX_SIZE = 1
    SIZE = 32


class TxoutToScript(x.MessageType):
    VARIANT_CODE = 0x0
    FIELDS = [
        ('keys', x.ContainerType, ECPoint),
        ('script', x.ContainerType, x.UInt8),
    ]


class TxoutToKey(x.MessageType):
    VARIANT_CODE = 0x2
    FIELDS = [
        ('key', ECPoint),
    ]


class TxoutTargetV(x.VariantType):
    FIELDS = [
        ('txout_to_script', TxoutToScript),
        ('txout_to_scripthash', x.UVarintType),
        ('txout_to_key', TxoutToKey),
    ]


class TxinGen(x.MessageType):
    VARIANT_CODE = 0xff
    FIELDS = [
        ('height', x.UVarintType),
    ]


class TxinToKey(x.MessageType):
    VARIANT_CODE = 0x2
    FIELDS = [
        ('amount', x.UVarintType),
        ('key_offsets', x.ContainerType, x.UVarintType),
        ('k_image', ECPoint),
    ]


class TxInV(x.VariantType):
    FIELDS = [
        ('txin_gen', TxinGen),
        ('txin_to_script', x.BlobType),
        ('txin_to_scripthash', x.BlobType),
        ('txin_to_key', TxinToKey),
    ]


class TxOut(x.MessageType):
    FIELDS = [
        ('amount', x.UVarintType),
        ('target', TxoutTargetV),
    ]


class TransactionPrefix(x.MessageType):
    FIELDS = [
        ('version', x.UVarintType),
        ('unlock_time', x.UVarintType),
        ('vin', x.ContainerType, TxInV),
        ('vout', x.ContainerType, TxOut),
        ('extra', x.ContainerType, x.UInt8),
    ]


class Transaction(TransactionPrefix):
    # TODO: tsx
    FIELDS = [

    ]

#
# rctTypes.h
#


class Key64(x.ContainerType):
    FIX_SIZE = 1
    SIZE = 64
    ELEM_TYPE = ECKey


class KeyV(x.ContainerType):
    FIX_SIZE = 0
    ELEM_TYPE = ECKey


class KeyM(x.ContainerType):
    FIX_SIZE = 0
    ELEM_TYPE = KeyV


class KeyVFix(x.ContainerType):
    FIX_SIZE = 1
    ELEM_TYPE = ECKey


class KeyMFix(x.ContainerType):
    FIX_SIZE = 1
    ELEM_TYPE = KeyVFix


class CtKey(x.MessageType):
    FIELDS = [
        ('dest', ECKey),
        ('mask', ECKey),
    ]


class CtkeyV(x.ContainerType):
    FIX_SIZE = 0
    ELEM_TYPE = CtKey


class CtkeyM(x.ContainerType):
    FIX_SIZE = 0
    ELEM_TYPE = CtkeyV


class MultisigKLRki(x.MessageType):
    FIELDS = [
        ('K', ECKey),
        ('L', ECKey),
        ('R', ECKey),
        ('ki', ECKey),
    ]


class MultisigOut(x.MessageType):
    FIELDS = [
        ('c', x.ContainerType, ECKey),
    ]


class EcdhTuple(x.MessageType):
    FIELDS = [
        ('mask', ECKey),
        ('amount', ECKey),
    ]


class BoroSig(x.MessageType):
    FIELDS = [
        ('s0', Key64),
        ('s1', Key64),
        ('ee', ECKey),
    ]


class MgSig(x.MessageType):
    __slots__ = ['ss', 'cc', 'II']
    FIELDS = [
        ('ss', KeyM),
        ('cc', ECKey),
    ]


class RangeSig(x.MessageType):
    __slots__ = ['asig', 'Ci']
    FIELDS = [
        ('asig', BoroSig),
        ('Ci', Key64),
    ]


class Bulletproof(x.MessageType):
    __slots__ = ['V', 'A', 'S', 'T1', 'T2', 'taux', 'mu', 'L', 'R', 'a', 'b', 't']
    FIELDS = [
        ('A', ECKey),
        ('S', ECKey),
        ('T1', ECKey),
        ('T2', ECKey),
        ('taux', ECKey),
        ('mu', ECKey),
        ('L', KeyV),
        ('R', KeyV),
        ('a', ECKey),
        ('b', ECKey),
        ('t', ECKey),
    ]


class RctSigBase(x.MessageType):
    __slots__ = ['V', 'A', 'S', 'T1', 'T2', 'taux', 'mu', 'L', 'R', 'a', 'b', 't']
    FIELDS = [
        ('type', x.UInt8),
        ('txnFee', x.UVarintType),
        ('message', ECKey),
        ('mixRing', CtkeyM),
        ('pseudoOuts', KeyV),
        ('ecdhInfo', x.ContainerType, EcdhTuple),
        ('outPk', CtkeyV),
    ]

    def serialize_archive(self, ar):
        """
        Custom serialization
        :param ar:
        :type ar: x.Archive
        :return:
        """
        # TODO: impl


class RctType(object):
    Null = 0
    Full = 1
    Simple = 2
    FullBulletproof = 3
    SimpleBulletproof = 4


class RctSigPrunable(x.MessageType):
    __slots__ = ['rangeSigs', 'bulletproofs', 'MGs', 'pseudoOuts']
    FIELDS = [
        ('rangeSigs', x.ContainerType, RangeSig),
        ('bulletproofs', x.ContainerType, Bulletproof),
        ('MGs', x.ContainerType, MgSig),
        ('pseudoOuts', KeyV),
    ]

    async def serialize_rctsig_prunable(self, ar, type, inputs, outputs, mixin):
        """
        Serialize rct sig
        :param ar:
        :type ar: x.Archive
        :param type:
        :param inputs:
        :param outputs:
        :param mixin:
        :return:
        """
        if type == RctType.Null:
            return True

        if type != RctType.Full and type != RctType.FullBulletproof and \
                type != RctType.Simple and type != RctType.SimpleBulletproof:
            raise ValueError('Unknown type')

        if type == RctType.SimpleBulletproof or type == RctType.FullBulletproof:
            ar.tag('bp')
            if len(self.bulletproofs) != outputs:
                raise ValueError('Bulletproofs size mismatch')

            ar.prepare_container(outputs, (x.ElemRefObj, self, 'bulletproofs'), elem_type=Bulletproof)
            for i in range(len(self.bulletproofs)):
                ar.field(elem=(x.ElemRefArr, self.bulletproofs, i), elem_type=Bulletproof)

        else:
            ar.tag('rangeSigs')
            if len(self.rangeSigs) != outputs:
                raise ValueError('rangeSigs size mismatch')

            ar.prepare_container(outputs, (x.ElemRefObj, self, 'rangeSigs'), elem_type=RangeSig)
            for i in range(len(self.rangeSigs)):
                ar.field(elem=(x.ElemRefArr, self.rangeSigs, i), elem_type=RangeSig)

        ar.tag('MGs')

        # We keep a byte for size of MGs, because we don't know whether this is
        # a simple or full rct signature, and it's starting to annoy the hell out of me
        mg_elements = inputs if type == RctType.Simple or type == RctType.SimpleBulletproof else 1
        if len(self.MGs) != mg_elements:
            raise ValueError('MGs size mismatch')

        ar.prepare_container(mg_elements, (x.ElemRefObj, self, 'MGs'), elem_type=MgSig)
        for i in range(mg_elements):
            # we save the MGs contents directly, because we want it to save its
            # arrays and matrices without the size prefixes, and the load can't
            # know what size to expect if it's not in the data
            ar.tag('ss')
            if ar.writing and len(self.MGs[i].ss) != mixin + 1:
                raise ValueError('MGs size mismatch')

            ar.prepare_container(mg_elements, (x.ElemRefObj, self.MGs[i], 'ss'), elem_type=KeyM)
            for j in range(mixin + 1):
                mg_ss2_elements = 1 + (1 if type == RctType.Simple or type == RctType.SimpleBulletproof else inputs)
                ar.prepare_container(mg_ss2_elements, (x.ElemRefArr, self.MGs[i].ss, j), elem_type=KeyM.ELEM_TYPE)

                if ar.writing and len(self.MGs[i].ss[j] != mg_ss2_elements):
                    raise ValueError('MGs size mismatch 2')

                for k in range(mg_ss2_elements):
                    ar.field((x.ElemRefArr, self.MGs[i].ss[j], k), elem_type=KeyM.ELEM_TYPE)

            ar.tag('cc')
            ar.field((x.ElemRefObj, self.MGs[i], 'cc'), elem_type=ECKey)

        if type == RctType.SimpleBulletproof:
            ar.prepare_container(inputs, (x.ElemRefObj, self, 'pseudoOuts'), elem_type=KeyV)
            if ar.writing and len(self.pseudoOuts) != inputs:
                raise ValueError('pseudoOuts size mismatch')

            for i in range(inputs):
                ar.field((x.ElemRefArr, self.pseudoOuts, i), elem_type=KeyV.ELEM_TYPE)








