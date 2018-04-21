#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import base64
import unittest
import binascii
import json
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
        data_bin = base64.b16decode(data_hex, True)
        reader = x.MemoryReaderWriter(bytearray(data_bin))
        ar = xmrb.Archive(reader, False)

        msg = xmr.TxinGen()
        await ar.root_message(msg)
        self.assertEqual(msg.height, 0x34)

    async def test_ctkey_msg(self):
        """
        CtKey
        :return:
        """
        data_hex = b'011673657269616c697a6174696f6e3a3a617263686976650000000000000120000000000000000000000000000000000000000000000000000000000000000001200000000000000000000000000000000000000000000000000000000000000000'
        data_bin = base64.b16decode(data_hex, True)
        reader = x.MemoryReaderWriter(bytearray(data_bin))
        ar = xmrb.Archive(reader, False)

        msg = xmr.CtKey()
        await ar.root_message(msg)

    async def test_destination_entries(self):
        """
        Tx destinations, two records, versioning test.
        :return:
        """
        data_hex = b'011673657269616c697a6174696f6e3a3a6172636869766500000001010144000000000120cc000000000000000000000000000000000000000000000000000000000000ee0120aa000000000000000000000000000000000000000000000000000000000000dd01010122012011000000000000000000000000000000000000000000000000000000000000ee012033000000000000000000000000000000000000000000000000000000000000dd00'
        data_bin = base64.b16decode(data_hex, True)
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

    async def test_tx_prefix(self):
        """
        Tx destinations, two records, versioning test.
        :return:
        """
        data_hex = b'011673657269616c697a6174696f6e3a3a617263686976650000000001020000000101000000010300000001070002bd02021e01012402000101ed019b01380000012001000000000000000000000000000000000000000000000000000000000000000000010200000000000001020000000001208829dedf62f2c7e6b21556daed786143fb4c1c3ff95bde568b82860229c44b17000102012098d2c70dcef9fc62378ed2d49301a800f90cd8c9423c2b08dfef5f9635267978012c000209012f3413399032aeea0173e1bdbff7ceb9f62089f1cd1163aa48e2226ce9077d5abe11ce95cad8f34e0d'
        data_bin = base64.b16decode(data_hex, True)
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
        self.assertEqual(msg.extra, [ 2, 9, 1, 47, 52, 19, 57, 144, 50, 174, 234, 1, 115, 225, 189, 191, 247, 206, 185, 246, 32, 137, 241, 205, 17, 99, 170, 72, 226, 34, 108, 233, 7, 125, 90, 190, 17, 206, 149, 202, 216, 243, 78, 13])






if __name__ == "__main__":
    unittest.main()  # pragma: no cover



