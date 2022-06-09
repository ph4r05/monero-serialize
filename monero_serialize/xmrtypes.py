#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
XMR types
'''


from . import xmrserialize as x
from . import xmrrpc
from .xmrserialize import eref
from .core import versioning


#
# cryptonote_basic.h
#


class Hash(x.BlobType):
    __slots__ = ['data']
    DATA_ATTR = 'data'
    FIX_SIZE = 1
    SIZE = 32


class Hash8(x.BlobType):
    __slots__ = ['data']
    DATA_ATTR = 'data'
    FIX_SIZE = 1
    SIZE = 8


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


class SecretKey(ECKey):
    __slots__ = ['bytes']


class ECPublicKey(ECPoint):
    __slots__ = ['data']


class KeyImage(ECPoint):
    __slots__ = ['data']


class KeyDerivation(ECPoint):
    __slots__ = ['data']


class UnorderedSet(x.ContainerType):
    pass


class TxoutToScript(x.MessageType):
    __slots__ = ['keys', 'script']
    VARIANT_CODE = 0x0
    MFIELDS = [
        ('keys', x.ContainerType, ECPublicKey),
        ('script', x.ContainerType, x.UInt8),
    ]


class TxoutToKey(x.MessageType):
    __slots__ = ['key']
    VARIANT_CODE = 0x2
    MFIELDS = [
        ('key', ECPublicKey),
    ]


class TxoutToScriptHash(x.MessageType):
    __slots__ = ['hash']
    VARIANT_CODE = 0x1
    MFIELDS = [
        ('hash', Hash),
    ]


class TxoutTargetV(x.VariantType):
    MFIELDS = [
        ('txout_to_script', TxoutToScript),
        ('txout_to_scripthash', TxoutToScriptHash),
        ('txout_to_key', TxoutToKey),
    ]


class TxinGen(x.MessageType):
    __slots__ = ['height']
    VARIANT_CODE = 0xff
    BOOST_VARIANT_CODE = 0x0
    MFIELDS = [
        ('height', x.UVarintType),
    ]


class TxinToKey(x.MessageType):
    __slots__ = ['amount', 'key_offsets', 'k_image']
    VARIANT_CODE = 0x2
    BOOST_VARIANT_CODE = 0x3
    MFIELDS = [
        ('amount', x.UVarintType),
        ('key_offsets', x.ContainerType, x.UVarintType),
        ('k_image', KeyImage),
    ]


class TxinToScript(x.MessageType):
    __slots__ = []
    VARIANT_CODE = 0x0
    BOOST_VARIANT_CODE = 0x1
    MFIELDS = []


class TxinToScriptHash(x.MessageType):
    __slots__ = []
    VARIANT_CODE = 0x1
    BOOST_VARIANT_CODE = 0x2
    MFIELDS = []


class TxInV(x.VariantType):
    MFIELDS = [
        ('txin_gen', TxinGen),
        ('txin_to_script', TxinToScript),
        ('txin_to_scripthash', TxinToScriptHash),
        ('txin_to_key', TxinToKey),
    ]


class TxOut(x.MessageType):
    __slots__ = ['amount', 'target']
    MFIELDS = [
        ('amount', x.UVarintType),
        ('target', TxoutTargetV),
    ]


class TransactionPrefix(x.MessageType):
    MFIELDS = [
        ('version', x.UVarintType),
        ('unlock_time', x.UVarintType),
        ('vin', x.ContainerType, TxInV),
        ('vout', x.ContainerType, TxOut),
        ('extra', x.ContainerType, x.UInt8),
    ]


class TransactionPrefixExtraBlob(TransactionPrefix):
    # noinspection PyTypeChecker
    MFIELDS = TransactionPrefix.MFIELDS[:-1] + [
        ('extra', x.BlobType),
    ]


#
# rctTypes.h
#


class Key64(x.ContainerType):
    FIX_SIZE = 1
    SIZE = 64
    BOOST_RAW_ARRAY = True
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
    __slots__ = ['dest', 'mask']
    MFIELDS = [
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
    MFIELDS = [
        ('K', ECKey),
        ('L', ECKey),
        ('R', ECKey),
        ('ki', ECKey),
    ]


class MultisigOut(x.MessageType):
    MFIELDS = [
        ('c', x.ContainerType, ECKey),
    ]


class EcdhTuple(x.MessageType):
    __slots__ = ['mask', 'amount']
    MFIELDS = [
        ('mask', ECKey),
        ('amount', ECKey),
    ]


class BoroSig(x.MessageType):
    __slots__ = ['s0', 's1', 'ee']
    MFIELDS = [
        ('s0', Key64),
        ('s1', Key64),
        ('ee', ECKey),
    ]


class MgSig(x.MessageType):
    __slots__ = ['ss', 'cc', 'II']
    MFIELDS = [
        ('ss', KeyM),
        ('cc', ECKey),
    ]


class CLSAG(x.MessageType):
    __slots__ = ['s', 'c1', 'I', 'D']
    MFIELDS = [
        ('s', KeyV),
        ('c1', ECKey),
        ('D', ECKey),
    ]


class RangeSig(x.MessageType):
    __slots__ = ['asig', 'Ci']
    MFIELDS = [
        ('asig', BoroSig),
        ('Ci', Key64),
    ]


class Bulletproof(x.MessageType):
    __slots__ = ['V', 'A', 'S', 'T1', 'T2', 'taux', 'mu', 'L', 'R', 'a', 'b', 't']
    MFIELDS = [
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

    async def boost_serialize(self, ar, version=None):
        await ar.message_fields(self, [('V', KeyV)] + self.MFIELDS)
        return self


class BulletproofPlus(x.MessageType):
    __slots__ = ['V', "A", "A1", "B", "r1", "s1", "d1", "V", "L", "R"]
    MFIELDS = [
        ("A", ECKey),
        ("A1", ECKey),
        ("B", ECKey),
        ("r1", ECKey),
        ("s1", ECKey),
        ("d1", ECKey),
        ("L", KeyV),
        ("R", KeyV),
    ]

    async def boost_serialize(self, ar, version=None):
        await ar.message_fields(self, [('V', KeyV)] + self.MFIELDS)
        return self


class EcdhInfo(x.ContainerType):
    ELEM_TYPE = EcdhTuple


async def boost_out_pk(ar, out_pk, version):
    if ar.writing:
        out_pk_m = [k.mask for k in x.get_elem(out_pk)]
        await ar.field(out_pk_m, KeyV)

    else:
        outs = await ar.field(None, KeyV)
        pks = [CtKey(dest=b'\x01'+(b'\x00'*31), mask=k) for k in outs]
        x.set_elem(out_pk, pks)
        return pks


class RctSigBase(x.MessageType):
    __slots__ = ['type', 'txnFee', 'message', 'mixRing', 'pseudoOuts', 'ecdhInfo', 'outPk']
    MFIELDS = [
        ('type', x.UInt8),
        ('txnFee', x.UVarintType),
        ('message', ECKey),
        ('mixRing', CtkeyM),
        ('pseudoOuts', KeyV),
        ('ecdhInfo', EcdhInfo),
        ('outPk', CtkeyV),
    ]

    async def serialize_rctsig_base(self, ar, inputs, outputs):
        """
        Custom serialization
        :param ar:
        :type ar: x.Archive
        :return:
        """
        await self._msg_field(ar, idx=0)
        if self.type == RctType.Null:
            return
        if self.type != RctType.Full and self.type != RctType.FullBulletproof and \
                self.type != RctType.Simple and self.type != RctType.SimpleBulletproof and \
                self.type != RctType.Bulletproof and self.type != RctType.Bulletproof2 and \
                self.type != RctType.CLSAG and self.type != RctType.BulletproofPlus:
            raise ValueError('Unknown type')

        await self._msg_field(ar, idx=1)
        if self.type == RctType.Simple:
            await ar.tag('pseudoOuts')
            await ar.begin_array()
            await ar.prepare_container(inputs, eref(self, 'pseudoOuts'), KeyV)
            if ar.writing and len(self.pseudoOuts) != inputs:
                raise ValueError('pseudoOuts size mismatch')

            for i in range(inputs):
                await ar.field(eref(self.pseudoOuts, i), KeyV.ELEM_TYPE)
            await ar.end_array()

        await ar.tag('ecdhInfo')
        await ar.begin_array()
        await ar.prepare_container(outputs, eref(self, 'ecdhInfo'), EcdhTuple)
        if ar.writing and len(self.ecdhInfo) != outputs:
            raise ValueError('EcdhInfo size mismatch')

        for i in range(outputs):
            if self.type in (RctType.Bulletproof2, RctType.CLSAG, RctType.BulletproofPlus):
                am8 = [self.ecdhInfo[i].amount[0:8] if ar.writing else bytearray(0)]
                await ar.field(eref(am8, 0), Hash8)
                if not ar.writing:
                    x.set_elem(eref(self.ecdhInfo[i], 'amount'), am8[0] + bytearray(24))
                    x.set_elem(eref(self.ecdhInfo[i], 'mask'), bytearray(32))
            else:
                await ar.field(eref(self.ecdhInfo, i), EcdhInfo.ELEM_TYPE)
        await ar.end_array()

        await ar.tag('outPk')
        await ar.begin_array()
        await ar.prepare_container((outputs), eref(self, 'outPk'), CtKey)
        if ar.writing and len(self.outPk) != outputs:
            raise ValueError('outPk size mismatch')

        for i in range(outputs):
            await ar.field(eref(self.outPk[i], 'mask'), ECKey)
        await ar.end_array()

    async def boost_serialize(self, ar, version=None):
        await self._msg_field(ar, 'type')
        if self.type == RctType.Simple:
            await self._msg_field(ar, 'pseudoOuts')
        await self._msg_field(ar, 'ecdhInfo')
        await boost_out_pk(ar, eref(self, 'outPk'), version)
        await self._msg_field(ar, 'txnFee')
        return self


class RctType(object):
    Null = 0
    Full = 1
    Simple = 2
    Bulletproof = 3
    Bulletproof2 = 4
    CLSAG = 5
    BulletproofPlus = 6

    FullBulletproof = 3     # pre v9, deprecated
    SimpleBulletproof = 4   # pre v9, deprecated


def is_rct_bp(rct_type):
    return rct_type in (RctType.Bulletproof, RctType.Bulletproof2, RctType.CLSAG, RctType.BulletproofPlus)


class RctSigPrunable(x.MessageType):
    __slots__ = ['rangeSigs', 'bulletproofs', 'bulletproofs_plus', 'MGs', 'CLSAGs', 'pseudoOuts']
    MFIELDS = [
        ('rangeSigs', x.ContainerType, RangeSig),
        ('bulletproofs', x.ContainerType, Bulletproof),
        ('bulletproofs_plus', x.ContainerType, BulletproofPlus),
        ('MGs', x.ContainerType, MgSig),
        ('CLSAGs', x.ContainerType, CLSAG),
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

        if type != RctType.Full and type != RctType.Bulletproof and \
                type != RctType.Simple and type != RctType.Bulletproof2 and \
                type != RctType.CLSAG and type != RctType.BulletproofPlus:
            raise ValueError('Unknown type')

        if type == RctType.BulletproofPlus:
            bps = [0]
            if ar.writing:
                bps[0] = len(self.bulletproofs_plus)
            await ar.field(elem=eref(bps, 0), elem_type=x.UVarintType)

            await ar.tag('bpp')
            await ar.begin_array()
            await ar.prepare_container(bps[0], eref(self, 'bulletproofs_plus'), elem_type=BulletproofPlus)

            for i in range(bps[0]):
                await ar.field(elem=eref(self.bulletproofs_plus, i), elem_type=BulletproofPlus)
            await ar.end_array()

        elif is_rct_bp(type):
            await ar.tag('bp')
            await ar.begin_array()
            bps = [0]
            if ar.writing:
                bps[0] = len(self.bulletproofs)

            if type in (RctType.Bulletproof2, RctType.CLSAG):
                await ar.field(elem=eref(bps, 0), elem_type=x.UVarintType)
            else:
                await ar.field(elem=eref(bps, 0), elem_type=x.UInt32)

            await ar.prepare_container(bps[0], eref(self, 'bulletproofs'), elem_type=Bulletproof)

            for i in range(bps[0]):
                await ar.field(elem=eref(self.bulletproofs, i), elem_type=Bulletproof)
            await ar.end_array()

        else:
            await ar.tag('rangeSigs')
            await ar.begin_array()
            await ar.prepare_container(outputs, eref(self, 'rangeSigs'), elem_type=RangeSig)
            if len(self.rangeSigs) != outputs:
                raise ValueError('rangeSigs size mismatch')

            for i in range(len(self.rangeSigs)):
                await ar.field(elem=eref(self.rangeSigs, i), elem_type=RangeSig)
            await ar.end_array()

        if type in (RctType.CLSAG, RctType.BulletproofPlus):
            await ar.tag('CLSAGs')
            await ar.begin_array()
            await ar.prepare_container(inputs, eref(self, 'CLSAGs'), elem_type=CLSAG)
            if len(self.CLSAGs) != inputs:
                raise ValueError('CLSAGs size mismatch')

            for i in range(inputs):
                # We save the CLSAGs contents directly, because we want it to save its
                # arrays without the size prefixes, and the load can't know what size
                # to expect if it's not in the data
                await ar.begin_object()
                await ar.tag('s')
                await ar.begin_array()
                await ar.prepare_container(mixin + 1, eref(self.CLSAGs[i], 's'), elem_type=KeyV)
                if len(self.CLSAGs[i].s) != mixin + 1:
                    raise ValueError('CLSAGs[i].s size mismatch')

                for j in range(mixin + 1):
                    await ar.field(eref(self.CLSAGs[i].s, j), elem_type=KeyV.ELEM_TYPE)
                await ar.end_array()

                await ar.tag('c1')
                await ar.field(eref(self.CLSAGs[i], 'c1'), elem_type=ECKey)
                await ar.tag('D')
                await ar.field(eref(self.CLSAGs[i], 'D'), elem_type=ECKey)
                await ar.end_object()

        else:
            await ar.tag('MGs')
            await ar.begin_array()

            # We keep a byte for size of MGs, because we don't know whether this is
            # a simple or full rct signature, and it's starting to annoy the hell out of me
            is_full = type == RctType.Full
            mg_elements = inputs if not is_full else 1
            await ar.prepare_container(mg_elements, eref(self, 'MGs'), elem_type=MgSig)
            if len(self.MGs) != mg_elements:
                raise ValueError('MGs size mismatch')

            for i in range(mg_elements):
                # We save the MGs contents directly, because we want it to save its
                # arrays and matrices without the size prefixes, and the load can't
                # know what size to expect if it's not in the data
                await ar.begin_object()
                await ar.tag('ss')
                await ar.begin_array()

                await ar.prepare_container(mixin + 1, eref(self.MGs[i], 'ss'), elem_type=KeyM)
                if ar.writing and len(self.MGs[i].ss) != mixin + 1:
                    raise ValueError('MGs size mismatch')

                for j in range(mixin + 1):
                    await ar.begin_array()
                    mg_ss2_elements = 1 + (1 if not is_full else inputs)
                    await ar.prepare_container(mg_ss2_elements, eref(self.MGs[i].ss, j), elem_type=KeyM.ELEM_TYPE)

                    if ar.writing and len(self.MGs[i].ss[j]) != mg_ss2_elements:
                        raise ValueError('MGs size mismatch 2')

                    for k in range(mg_ss2_elements):
                        await ar.field(eref(self.MGs[i].ss[j], k), elem_type=KeyV.ELEM_TYPE)
                    await ar.end_array()

                await ar.tag('cc')
                await ar.field(eref(self.MGs[i], 'cc'), elem_type=ECKey)
                await ar.end_object()
            await ar.end_array()

        if type in (RctType.Bulletproof, RctType.Bulletproof2, RctType.CLSAG, RctType.BulletproofPlus):
            await ar.begin_array()
            await ar.prepare_container(inputs, eref(self, 'pseudoOuts'), elem_type=KeyV)
            if ar.writing and len(self.pseudoOuts) != inputs:
                raise ValueError('pseudoOuts size mismatch')

            for i in range(inputs):
                await ar.field(eref(self.pseudoOuts, i), elem_type=KeyV.ELEM_TYPE)
            await ar.end_array()

    async def boost_serialize(self, ar, version):
        await self._msg_field(ar, 'rangeSigs')
        if self.rangeSigs is None or len(self.rangeSigs) == 0:
            await self._msg_field(ar, 'bulletproofs')
        await self._msg_field(ar, 'MGs')
        if self.rangeSigs is None or len(self.rangeSigs) == 0:
            await self._msg_field(ar, 'pseudoOuts')
        return self


class RctSig(RctSigBase):
    # noinspection PyTypeChecker
    MFIELDS = RctSigBase.MFIELDS + [
        ('p', RctSigPrunable),
    ]


class Signature(x.MessageType):
    __slots__ = ['c', 'r']
    MFIELDS = [
        ('c', ECKey),
        ('r', ECKey),
    ]

    async def serialize_archive(self, ar, version=None):
        ar.field(eref(self, 'c'), ECKey)
        ar.field(eref(self, 'r'), ECKey)
        return self


class SignatureArray(x.ContainerType):
    FIX_SIZE = 0
    ELEM_TYPE = Signature


def get_signature_size(msg):
    """
    Returns a signature size for the input
    :param msg:
    :return:
    """
    if isinstance(msg, (TxinGen, TxinToScript, TxinToScriptHash)):
        return 0
    elif isinstance(msg, TxinToKey):
        return len(msg.key_offsets)
    else:
        raise ValueError('Unknown tx in')


class Transaction(TransactionPrefix):
    # noinspection PyTypeChecker
    MFIELDS = TransactionPrefix.MFIELDS + [
        ('signatures', x.ContainerType, SignatureArray),
        ('rct_signatures', RctSig),
    ]

    async def serialize_archive(self, ar, version=None):
        """
        Serialize the transaction
        :param ar:
        :type ar: x.Archive
        :return:
        """
        # Transaction prefix serialization first.
        await ar.message(self, TransactionPrefix)

        if self.version == 1:
            await ar.tag('signatures')
            await ar.begin_array()
            await ar.prepare_container(len(self.vin), eref(self, 'signatures'), elem_type=SignatureArray)
            signatures_not_expected = len(self.signatures) == 0
            if not signatures_not_expected and len(self.vin) != len(self.signatures):
                raise ValueError('Signature size mismatch')

            for i in range(len(self.vin)):
                sig_size = get_signature_size(self.vin[i])
                if signatures_not_expected:
                    if 0 == sig_size:
                        continue
                    else:
                        raise ValueError('Unexpected sig')

                await ar.prepare_container(sig_size, eref(self.signatures, i), elem_type=SignatureArray)
                if sig_size != len(self.signatures[i]):
                    raise ValueError('Unexpected sig size')

                for j in range(sig_size):
                    await ar.field(eref(self.signatures[i], j), Signature)

        else:
            await ar.tag('rct_signatures')
            if len(self.vin) == 0:
                return

            await ar.begin_object()
            await ar.prepare_message(eref(self, 'rct_signatures'), RctSig)
            await self.rct_signatures.serialize_rctsig_base(ar, len(self.vin), len(self.vout))
            await ar.end_object()

            if self.rct_signatures.type != RctType.Null:
                mixin_size = len(self.vin[0].key_offsets) - 1 if len(self.vin) > 0 and isinstance(self.vin[0], TxinToKey) else 0
                await ar.tag('rctsig_prunable')
                await ar.begin_object()
                await ar.prepare_message(eref(self.rct_signatures, 'p'), RctSigPrunable)
                await self.rct_signatures.p.serialize_rctsig_prunable(ar, self.rct_signatures.type,
                                                                      len(self.vin), len(self.vout),
                                                                      mixin_size)
                await ar.end_object()
        return self

    async def boost_serialize(self, ar, version):
        await ar.message(self, TransactionPrefix, use_version=version)

        if self.version == 1:
            raise ValueError('TxV1 not supported')

        else:
            await ar.prepare_message(eref(self, 'rct_signatures'), RctSigBase)
            await ar.message(self.rct_signatures, RctSigBase)
            if self.rct_signatures.type != RctType.Null:
                await ar.prepare_message(eref(self.rct_signatures, 'p'), RctSigPrunable)
                await ar.message(self.rct_signatures.p, RctSigPrunable)
        return self


class BlockHeader(x.MessageType):
    MFIELDS = [
        ('major_version', x.UVarintType),  # x.UInt8
        ('minor_version', x.UVarintType),  # x.UInt8
        ('timestamp', x.UVarintType),  # x.UInt64
        ('prev_id', Hash),
        ('nonce', x.UInt32),
    ]


class HashVector(x.ContainerType):
    ELEM_TYPE = Hash


class Block(BlockHeader):
    # noinspection PyTypeChecker
    MFIELDS = BlockHeader.MFIELDS + [
        ('miner_tx', Transaction),
        ('tx_hashes', HashVector),
    ]


class TransactionMetaData(x.MessageType):
    MFIELDS = [
        ('tx_id', x.UInt64),
        ('unlock_time', x.UInt64),
        ('block_id', x.UInt64),
    ]


class TxIndex(x.MessageType):
    MFIELDS = [
        ('key', Hash),
        ('data', TransactionMetaData),
    ]


class AccountPublicAddress(x.MessageType):
    __slots__ = ['m_spend_public_key', 'm_view_public_key']
    MFIELDS = [
        ('m_spend_public_key', ECPublicKey),
        ('m_view_public_key', ECPublicKey),
    ]


class SubaddressIndex(x.MessageType):
    __slots__ = ['major', 'minor']
    MFIELDS = [
        ('major', x.UInt32),
        ('minor', x.UInt32),
    ]


class MultisigLR(x.MessageType):
    __slots__ = ['L', 'R']
    BOOST_VERSION = 0
    MFIELDS = [
        ('L', ECKey),
        ('R', ECKey),
    ]


class MultisigInfo(x.MessageType):
    __slots__ = ['signer', 'LR', 'partial_key_images']
    BOOST_VERSION = 1
    MFIELDS = [
        ('signer', ECPublicKey),
        ('LR', x.ContainerType, MultisigLR),
        ('partial_key_images', x.ContainerType, KeyImage),
    ]


class MultisigStruct(x.MessageType):
    __slots__ = ['sigs', 'ignore', 'used_L', 'signing_keys', 'msout']
    MFIELDS = [
        ('sigs', RctSig),
        ('ignore', ECPublicKey),
        ('used_L', x.ContainerType, ECKey),
        ('signing_keys', x.ContainerType, ECPublicKey),
        ('msout', MultisigOut),
    ]


class TxExtraPadding(x.MessageType):
    __slots__ = ['size']
    TX_EXTRA_PADDING_MAX_COUNT = 255

    VARIANT_CODE = 0x0
    MFIELDS = [
        ('size', x.SizeT),
    ]

    async def serialize_archive(self, ar, version=None):
        if ar.writing:
            if self.size > self.TX_EXTRA_PADDING_MAX_COUNT:
                raise ValueError('Padding too big')
            for i in range(self.size):
                ar.uint(0, x.UInt8)

        else:
            self.size = 0
            buffer = bytearray(1)
            for i in range(self.TX_EXTRA_PADDING_MAX_COUNT+1):
                self.size += 1
                try:
                    nread = await ar.iobj.areadinto(buffer)
                    if nread == 0:
                        break
                except EOFError:
                    break

                if buffer[0] != 0:
                    raise ValueError('Padding error')
        return self


class TxExtraPubKey(x.MessageType):
    __slots__ = ['pub_key']
    VARIANT_CODE = 0x1
    MFIELDS = [
        ('pub_key', ECPublicKey),
    ]


class TxExtraNonce(x.MessageType):
    __slots__ = ['nonce']
    VARIANT_CODE = 0x2
    MFIELDS = [
        ('nonce', x.BlobType),
    ]


class TxExtraMergeMiningTag(x.MessageType):
    VARIANT_CODE = 0x3
    MFIELDS = [
        ('field_len', x.UVarintType),
        ('depth', x.UVarintType),
        ('merkle_root', Hash),
    ]


class TxExtraAdditionalPubKeys(x.MessageType):
    __slots__ = ['data']
    VARIANT_CODE = 0x4
    MFIELDS = [
        ('data', x.ContainerType, ECPublicKey),
    ]


class TxExtraMysteriousMinergate(x.MessageType):
    __slots__ = ['data']
    VARIANT_CODE = 0xde
    MFIELDS = [
        ('data', x.BlobType),
    ]


class TxExtraField(x.VariantType):
    MFIELDS = [
        ('tx_extra_padding', TxExtraPadding),
        ('tx_extra_pub_key', TxExtraPubKey),
        ('tx_extra_nonce', TxExtraNonce),
        ('tx_extra_merge_mining_tag', TxExtraMergeMiningTag),
        ('tx_extra_additional_pub_keys', TxExtraAdditionalPubKeys),
        ('tx_extra_mysterious_minergate', TxExtraMysteriousMinergate),
    ]


class TxExtraFields(x.ContainerType):
    ELEM_TYPE = TxExtraField


class OutputEntry(x.TupleType):
    MFIELDS = [
        x.UVarintType, CtKey  # original: x.UInt64
    ]


class TxSourceEntry(x.MessageType):
    BOOST_VERSION = 1
    MFIELDS = [
        ('outputs', x.ContainerType, OutputEntry),
        ('real_output', x.SizeT),
        ('real_out_tx_key', ECPublicKey),
        ('real_out_additional_tx_keys', x.ContainerType, ECPublicKey),
        ('real_output_in_tx_index', x.UInt64),
        ('amount', x.UInt64),
        ('rct', x.BoolType),
        ('mask', ECKey),
        ('multisig_kLRki', MultisigKLRki),
    ]

    async def boost_serialize(self, ar, version):
        if version != 1:
            raise ValueError('TxSourceEntry v1 supported only')
        await self._msg_field(ar, 'outputs')
        await self._msg_field(ar, 'real_output')
        await self._msg_field(ar, 'real_out_tx_key')
        await self._msg_field(ar, 'real_output_in_tx_index')
        await self._msg_field(ar, 'amount')
        await self._msg_field(ar, 'rct')
        await self._msg_field(ar, 'mask')
        await self._msg_field(ar, 'multisig_kLRki')
        await self._msg_field(ar, 'real_out_additional_tx_keys')
        return self


class TxDestinationEntry(x.MessageType):
    __slots__ = ['amount', 'addr', 'is_subaddress', 'original', 'is_integrated']
    BC_VERSION = 1  # default blockchain version
    BOOST_VERSION = 2
    MFIELDS = [
        ('original', x.UnicodeType),  # original: UInt64
        ('amount', x.UVarintType),  # original: UInt64
        ('addr', AccountPublicAddress),
        ('is_subaddress', x.BoolType),
        ('is_integrated', x.BoolType),
    ]

    async def boost_serialize(self, ar, version):
        if version < 1 or version > self.BOOST_VERSION:
            raise ValueError('Unsupported version: %s' % version)
        await self._msg_field(ar, 'amount')
        await self._msg_field(ar, 'addr')
        await self._msg_field(ar, 'is_subaddress')
        if version < 2:
            self.is_integrated = 0
            return self

        await self._msg_field(ar, 'original')
        await self._msg_field(ar, 'is_integrated')
        return self

    async def serialize_archive(self, ar, version=None):
        if version is None:
            version = self.BOOST_VERSION

        fields = list(self.f_specs())
        if version < 2:
            self._rm_field(fields, 'original')
            self._rm_field(fields, 'is_integrated')

        await self._msg_fields(ar, fields)
        return self


class TransferDetailsUse(x.TupleType):
    MFIELDS = [
        x.SizeT, Hash
    ]


class TransferDetails(x.MessageType):
    BOOST_VERSION = 11
    MFIELDS = [
        ('m_block_height', x.UInt64),
        ('m_tx', TransactionPrefix),
        ('m_txid', Hash),
        ('m_internal_output_index', x.SizeT),
        ('m_global_output_index', x.UInt64),
        ('m_spent', x.BoolType),
        ('m_spent_height', x.UInt64),
        ('m_key_image', KeyImage),
        ('m_mask', ECKey),
        ('m_amount', x.UInt64),
        ('m_rct', x.BoolType),
        ('m_key_image_known', x.BoolType),
        ('m_key_image_requested', x.BoolType),
        ('m_pk_index', x.SizeT),
        ('m_subaddr_index', SubaddressIndex),
        ('m_key_image_partial', x.BoolType),
        ('m_multisig_k', x.ContainerType, ECKey),
        ('m_multisig_info', x.ContainerType, MultisigInfo),
        ('m_uses', x.ContainerType, TransferDetailsUse),
    ]

    async def boost_serialize(self, ar, version):
        if version < 9 or version > self.BOOST_VERSION:
            raise ValueError('TransferDetails unsupported version: %s' % version)
        await self._msg_field(ar, 'm_block_height')
        await self._msg_field(ar, 'm_global_output_index')
        await self._msg_field(ar, 'm_internal_output_index')
        await self._msg_field(ar, 'm_tx')
        await self._msg_field(ar, 'm_spent')
        await self._msg_field(ar, 'm_key_image')
        await self._msg_field(ar, 'm_mask')
        await self._msg_field(ar, 'm_amount')
        await self._msg_field(ar, 'm_spent_height')
        await self._msg_field(ar, 'm_txid')
        await self._msg_field(ar, 'm_rct')
        await self._msg_field(ar, 'm_key_image_known')
        await self._msg_field(ar, 'm_pk_index')
        await self._msg_field(ar, 'm_subaddr_index')
        await self._msg_field(ar, 'm_multisig_info')
        await self._msg_field(ar, 'm_multisig_k')
        await self._msg_field(ar, 'm_key_image_partial')
        if version < 10:
            self.m_key_image_requested = 0
            return self
        if version < 11:
            self.m_uses = []

        await self._msg_field(ar, 'm_key_image_requested')
        await self._msg_field(ar, 'm_uses')
        return self

    async def serialize_archive(self, ar, version=None):
        if version is None:
            version = self.BOOST_VERSION

        fields = list(self.f_specs())
        if version < 10:
            self._rm_field(fields, 'm_key_image_requested')
        if version < 11:
            self._rm_field(fields, 'm_uses')

        await self._msg_fields(ar, fields)
        return self


class RCTConfig(x.MessageType):
    MFIELDS = [
        ('range_proof_type', x.UVarintType),
        ('bp_version', x.UVarintType),
    ]


class TxConstructionData(x.MessageType):
    BOOST_VERSION = 4
    MFIELDS = [
        ('sources', x.ContainerType, TxSourceEntry),
        ('change_dts', TxDestinationEntry),
        ('splitted_dsts', x.ContainerType, TxDestinationEntry),
        ('selected_transfers', x.ContainerType, x.SizeT),
        ('extra', x.ContainerType, x.UInt8),
        ('unlock_time', x.UInt64),
        ('use_rct', x.BoolType),
        ('use_bulletproofs', x.BoolType),
        ('rct_config', RCTConfig),
        ('dests', x.ContainerType, TxDestinationEntry),
        ('subaddr_account', x.UInt32),
        ('subaddr_indices', x.ContainerType, x.UVarintType),  # original: x.UInt32
    ]

    async def boost_serialize(self, ar, version):
        if version < 2 or version > self.BOOST_VERSION:
            raise ValueError('TXConstruction unsupported version: %s' % version)
        await self._msg_field(ar, 'sources')
        await self._msg_field(ar, 'change_dts')
        await self._msg_field(ar, 'splitted_dsts')
        await self._msg_field(ar, 'extra')
        await self._msg_field(ar, 'unlock_time')
        await self._msg_field(ar, 'use_rct')
        await self._msg_field(ar, 'dests')
        await self._msg_field(ar, 'subaddr_account')
        await self._msg_field(ar, 'subaddr_indices')
        await self._msg_field(ar, 'selected_transfers')
        if version >= 3:
            await ar.message_field(self, ('use_bulletproofs', x.BoolType))
        return self.postprocess(version)

    async def serialize_archive(self, ar, version=None):
        if version is None:
            version = self.BOOST_VERSION

        fields = list(self.f_specs())

        if version == 4 or version < 3:
            self._rm_field(fields, 'use_bulletproofs')
        if version < 4:
            self._rm_field(fields, 'rct_config')

        await self._msg_fields(ar, fields)
        return self.postprocess(version)

    def postprocess(self, version):
        if version == 3:
            self.rct_config = RCTConfig(range_proof_type=1 if self.use_bulletproofs else 0, bp_version=0)
        if version == 4:
            self.use_bulletproofs = self.rct_config.range_proof_type != 0
        return self


class PendingTransaction(x.MessageType):
    BOOST_VERSION = 3
    MFIELDS = [
        ('tx', Transaction),
        ('dust', x.UInt64),
        ('fee', x.UInt64),
        ('dust_added_to_fee', x.BoolType),
        ('change_dts', TxDestinationEntry),
        ('selected_transfers', x.ContainerType, x.SizeT),
        ('key_images', x.UnicodeType),
        ('tx_key', SecretKey),
        ('additional_tx_keys', x.ContainerType, SecretKey),
        ('dests', x.ContainerType, TxDestinationEntry),
        ('multisig_sigs', x.ContainerType, MultisigStruct),
        ('construction_data', TxConstructionData),
    ]

    async def boost_serialize(self, ar, version):
        if version != 3:
            raise ValueError('Pending transaction v3+ supported only')
        await self._msg_field(ar, idx=0)
        await self._msg_field(ar, idx=1)
        await self._msg_field(ar, idx=2)
        await self._msg_field(ar, idx=3)
        await self._msg_field(ar, idx=4)
        await self._msg_field(ar, 'key_images')
        await self._msg_field(ar, 'tx_key')
        await self._msg_field(ar, 'dests')
        await self._msg_field(ar, 'construction_data')
        await self._msg_field(ar, 'additional_tx_keys')
        await self._msg_field(ar, 'selected_transfers')
        await self._msg_field(ar, 'multisig_sigs')
        return self


class PendingTransactionVector(x.ContainerType):
    ELEM_TYPE = PendingTransaction


class UnsignedTxSet(x.MessageType):
    BOOST_VERSION = 0
    MFIELDS = [
        ('txes', x.ContainerType, TxConstructionData),
        ('transfers', x.ContainerType, TransferDetails),
    ]


class SignedTxSet(x.MessageType):
    BOOST_VERSION = 0
    MFIELDS = [
        ('ptx', PendingTransactionVector),
        ('key_images', x.ContainerType, KeyImage),
    ]


class MultisigTxSet(x.MessageType):
    BOOST_VERSION = 0
    MFIELDS = [
        ('m_ptx', PendingTransactionVector),
        ('m_signers', UnorderedSet, ECPublicKey),
    ]


class ChachaIv(x.BlobType):
    FIX_SIZE = 1
    SIZE = 8


class KeysFileData(x.MessageType):
    MFIELDS = [
        ('iv', ChachaIv),
        ('account_data', x.BlobType),
    ]


class CacheFileData(x.MessageType):
    MFIELDS = [
        ('iv', ChachaIv),
        ('cache_data', x.BlobType),
    ]


class AccountKeys(x.MessageType):
    MFIELDS = [
        ('m_account_address', AccountPublicAddress),
        ('m_spend_secret_key', SecretKey),
        ('m_view_secret_key', SecretKey),
        ('m_multisig_keys', x.ContainerType, SecretKey),
    ]

    async def kv_serialize(self, ar, obj=None, **kwargs):
        await self._msg_field(ar, 'm_account_address', obj=obj)
        await self._msg_field(ar, 'm_spend_secret_key', obj=obj)
        await self._msg_field(ar, 'm_view_secret_key', obj=obj)
        await ar.message_field(self, ('m_multisig_keys', xmrrpc.BlobFieldWrapper(x.ContainerType), SecretKey), obj=obj)
        return obj


class WalletKeyData(x.MessageType):
    MFIELDS = [
        ('m_creation_timestamp', x.UInt64),
        ('m_keys', AccountKeys),
    ]


def hf_versions(hf=9):
    vers = {}
    if hf <= 9:
        vers[TxDestinationEntry] = 1
        vers[TxConstructionData] = 2
        vers[TransferDetails] = 9
        vers[SignedTxSet] = 0

    elif hf >= 10:
        vers[TxDestinationEntry] = 2
        vers[TxConstructionData] = 3
        vers[TransferDetails] = 10
        vers[SignedTxSet] = 0
        vers[TxConstructionData] = 3

    elif hf >= 11:
        vers[TransferDetails] = 11
        vers[SignedTxSet] = 0  # TODO: impl 1, unordered_map
        vers[TxConstructionData] = 4

    vers[MultisigLR] = 0
    vers[MultisigInfo] = 1
    vers[TxSourceEntry] = 1
    vers[PendingTransaction] = 3
    vers[UnsignedTxSet] = 0
    vers[SignedTxSet] = 0
    vers[MultisigTxSet] = 0
    return versioning.VersionSetting(vers)

