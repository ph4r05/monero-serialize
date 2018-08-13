#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import unittest
import binascii
import json
import os
import pkg_resources

import asyncio
import aiounittest

from .test_data import XmrTestData
from .. import xmrserialize as x
from .. import xmrtypes as xmr
from .. import xmrboost as xmrb
from .. import xmrobj as xmro
from .. import xmrjson as xmrjs


__author__ = 'dusanklinec'


class XmrBoostTest(aiounittest.AsyncTestCase):
    """Simple tests"""

    def __init__(self, *args, **kwargs):
        super(XmrBoostTest, self).__init__(*args, **kwargs)
        self.test_data = XmrTestData()

    def setUp(self):
            self.test_data.reset()

    async def test_simple_msg(self):
        """
        TxinGen
        :return:
        """
        data_hex = b'011673657269616c697a6174696f6e3a3a61726368697665000000000134'
        data_bin = binascii.unhexlify(data_hex)
        reader = x.MemoryReaderWriter(bytearray(data_bin))
        ar = xmrb.Archive(reader, False)

        msg = xmr.TxinGen()
        await ar.root_message(msg)
        self.assertEqual(msg.height, 0x34)

        writer = x.MemoryReaderWriter()
        ar2 = xmrb.Archive(writer, True)
        await ar2.root()
        await ar2.message(msg)
        self.assertEqual(data_bin, bytearray(writer.get_buffer()))

    async def test_ctkey_msg(self):
        """
        CtKey
        :return:
        """
        data_hex = b'011673657269616c697a6174696f6e3a3a617263686976650000000000000120000000000000000000000000000000000000000000000000000000000000000001200000000000000000000000000000000000000000000000000000000000000000'
        data_bin = binascii.unhexlify(data_hex)
        reader = x.MemoryReaderWriter(bytearray(data_bin))
        ar = xmrb.Archive(reader, False)

        msg = xmr.CtKey()
        await ar.root_message(msg)

        writer = x.MemoryReaderWriter()
        ar2 = xmrb.Archive(writer, True)
        await ar2.root()
        await ar2.message(msg)
        self.assertEqual(data_bin, bytearray(writer.get_buffer()))

    async def test_destination_entries(self):
        """
        Tx destinations, two records, versioning test.
        :return:
        """
        data_hex = b'011673657269616c697a6174696f6e3a3a6172636869766500000001010144000000000120cc000000000000000000000000000000000000000000000000000000000000ee0120aa000000000000000000000000000000000000000000000000000000000000dd01010122012011000000000000000000000000000000000000000000000000000000000000ee012033000000000000000000000000000000000000000000000000000000000000dd00'
        data_bin = binascii.unhexlify(data_hex)
        reader = x.MemoryReaderWriter(bytearray(data_bin))
        ar = xmrb.Archive(reader, False)

        msg = xmr.TxDestinationEntry()
        await ar.root_message(msg)

        self.assertEqual(msg.amount, 0x44)
        self.assertEqual(msg.is_subaddress, 1)
        self.assertEqual(msg.addr.m_spend_public_key, bytearray(b'\xcc' + (b'\x00' * 30) + b'\xee'))
        self.assertEqual(msg.addr.m_view_public_key, bytearray(b'\xaa' + (b'\x00' * 30) + b'\xdd'))

        msg2 = xmr.TxDestinationEntry()
        await ar.message(msg2)

        self.assertEqual(msg2.amount, 0x22)
        self.assertEqual(msg2.is_subaddress, 0)
        self.assertEqual(msg2.addr.m_spend_public_key, bytearray(b'\x11' + (b'\x00' * 30) + b'\xee'))
        self.assertEqual(msg2.addr.m_view_public_key, bytearray(b'\x33' + (b'\x00' * 30) + b'\xdd'))

        writer = x.MemoryReaderWriter()
        ar2 = xmrb.Archive(writer, True)
        await ar2.root()
        await ar2.message(msg)
        await ar2.message(msg2)
        self.assertEqual(data_bin, bytearray(writer.get_buffer()))

    async def test_tx_prefix(self):
        """
        Transaction prefix
        :return:
        """
        data_hex = pkg_resources.resource_string(__name__, os.path.join('data', 'tx_prefix_01.txt'))
        data_bin = binascii.unhexlify(data_hex)
        reader = x.MemoryReaderWriter(bytearray(data_bin))
        ar = xmrb.Archive(reader, False)

        msg = xmr.TransactionPrefix()
        await ar.root()
        await ar.message(msg)
        self.assertEqual(msg.version, 2)
        self.assertEqual(msg.unlock_time, 0)
        self.assertEqual(len(msg.vin), 1)
        self.assertEqual(len(msg.vout), 2)
        self.assertEqual(len(msg.extra), 44)
        self.assertEqual(msg.vin[0].amount, 0)
        self.assertEqual(len(msg.vin[0].key_offsets), 7)
        self.assertEqual(msg.vin[0].key_offsets[6], 56)
        self.assertEqual(msg.vout[0].amount, 0)
        self.assertEqual(msg.vout[1].amount, 0)
        self.assertEqual(msg.vout[0].target.key,
                         binascii.unhexlify(b'8829dedf62f2c7e6b21556daed786143fb4c1c3ff95bde568b82860229c44b17'))
        self.assertEqual(msg.vout[1].target.key,
                         binascii.unhexlify(b'98d2c70dcef9fc62378ed2d49301a800f90cd8c9423c2b08dfef5f9635267978'))
        self.assertEqual(msg.extra, [2, 9, 1, 47, 52, 19, 57, 144, 50, 174, 234, 1, 115, 225, 189, 191, 247, 206, 185, 246, 32, 137, 241, 205, 17, 99, 170, 72, 226, 34, 108, 233, 7, 125, 90, 190, 17, 206, 149, 202, 216, 243, 78, 13])

        writer = x.MemoryReaderWriter()
        ar2 = xmrb.Archive(writer, True)
        await ar2.root()
        await ar2.message(msg)
        self.assertEqual(data_bin, bytearray(writer.get_buffer()))

    async def test_tx(self):
        """
        Full transaction
        :return:
        """
        data_hex = pkg_resources.resource_string(__name__, os.path.join('data', 'tx_01.txt'))
        data_bin = binascii.unhexlify(data_hex)
        reader = x.MemoryReaderWriter(bytearray(data_bin))
        ar = xmrb.Archive(reader, False)

        msg = xmr.Transaction()
        await ar.root()
        await ar.message(msg)
        self.assertEqual(msg.version, 2)
        self.assertEqual(msg.unlock_time, 0)
        self.assertEqual(msg.rct_signatures.type, 1)
        self.assertEqual(msg.rct_signatures.txnFee, 9119110000)
        self.assertEqual(msg.rct_signatures.outPk[1].mask,
                         binascii.unhexlify(b'4908ea58bad7ed52bd70cc201eaae6280d833226bce333b16672c30ad91f9b43'))
        self.assertEqual(len(msg.rct_signatures.p.rangeSigs), 2)
        self.assertEqual(len(msg.rct_signatures.p.MGs), 1)
        self.assertEqual(len(msg.rct_signatures.p.MGs[0].ss), 7)
        self.assertEqual(msg.rct_signatures.p.MGs[0].cc,
                         binascii.unhexlify(b'23237696b7cfd0fe1159cfedd00a8acc138ef91f2f249e6289e1f14cb58bce06'))

        writer = x.MemoryReaderWriter()
        ar2 = xmrb.Archive(writer, True)
        await ar2.root()
        await ar2.message(msg)
        self.assertEqual(data_bin, bytearray(writer.get_buffer()))

    async def test_tx_metadata(self):
        """
        Tx metadata produced by watch-only wallet
        :return:
        """
        data_hex = pkg_resources.resource_string(__name__, os.path.join('data', 'tx_metadata_01.txt'))
        data_bin = binascii.unhexlify(data_hex)
        reader = x.MemoryReaderWriter(bytearray(data_bin))
        ar = xmrb.Archive(reader, False)

        msg = xmr.PendingTransaction()
        await ar.root()
        await ar.message(msg)

        self.assertEqual(msg.tx_key,
                         binascii.unhexlify(b'a0a50810dbc38101a79525823428b500ac936dfea613c73b4864f7260ff26a0b'))
        self.assertEqual(msg.change_dts.amount, 99972803971000)
        self.assertEqual(msg.fee, 9119110000)
        self.assertEqual(msg.construction_data.use_rct, 1)
        self.assertEqual(len(msg.construction_data.extra), 44)
        self.assertEqual(len(msg.construction_data.sources), 1)
        self.assertEqual(msg.construction_data.sources[0].amount, 100000000000000)
        self.assertEqual(msg.construction_data.sources[0].mask,
                         binascii.unhexlify(b'2dea8778cf4e89a7f32b5659d674d44795a370a00f79ee9b2ea37c1fcb005c0d'))
        self.assertEqual(len(msg.construction_data.sources[0].outputs), 7)
        self.assertEqual(msg.construction_data.sources[0].outputs[6][0], 1727)
        self.assertEqual(msg.construction_data.sources[0].outputs[6][1].mask,
                         binascii.unhexlify(b'2eeec82a970bfa54c35b0b740f6fb0585de14818e3c6dceed75c76fe69e3e449'))

        self.assertEqual(len(msg.construction_data.dests), 1)
        self.assertEqual(len(msg.construction_data.splitted_dsts), 2)
        self.assertEqual(msg.construction_data.splitted_dsts[0].amount, 18076919000)
        self.assertEqual(msg.construction_data.splitted_dsts[1].amount, 99972803971000)
        self.assertEqual(len(msg.construction_data.subaddr_indices), 1)

        msg.construction_data.use_bulletproofs = False
        writer = x.MemoryReaderWriter()
        ar2 = xmrb.Archive(writer, True)
        await ar2.root()
        await ar2.message(msg)
        # self.assertEqual(data_bin, bytearray(writer.get_buffer()))

    async def test_tx_unsigned(self):
        unsigned_tx_c = pkg_resources.resource_string(__name__, os.path.join('data', 'tx_unsigned_01.txt'))
        unsigned_tx = binascii.unhexlify(unsigned_tx_c)

        reader = x.MemoryReaderWriter(bytearray(unsigned_tx))
        ar = xmrb.Archive(reader, False)

        msg = xmr.UnsignedTxSet()
        await ar.root()
        await ar.message(msg)
        self.assertEqual(len(msg.transfers), 2)
        self.assertEqual(msg.transfers[0].m_block_height, 1998)
        self.assertEqual(msg.transfers[0].m_global_output_index, 701)
        self.assertEqual(msg.transfers[1].m_block_height, 3312)
        self.assertEqual(msg.transfers[1].m_global_output_index, 2026)
        self.assertEqual(msg.transfers[1].m_amount, 1000000000000000)
        self.assertEqual(msg.transfers[1].m_mask,
                         bytearray([0x5c,0x2f,0x4b,0x93,0x26,0xd1,0xa3,0xd8,0x17,0x0d,0x1e,0x5b,0x69,0xb5,0x19,0x2c,0xba,0x9d,0x7c,0x48,0xf2,0xc7,0xc3,0xcf,0xdd,0x9d,0x1b,0xbd,0x4f,0x96,0xeb,0x00]))

        for tx in msg.txes:
            tx.use_bulletproofs = False

        writer = x.MemoryReaderWriter()
        ar2 = xmrb.Archive(writer, True)
        await ar2.root()
        await ar2.message(msg)
        # self.assertEqual(unsigned_tx, bytearray(writer.get_buffer()))


if __name__ == "__main__":
    unittest.main()  # pragma: no cover



