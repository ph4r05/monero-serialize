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






if __name__ == "__main__":
    unittest.main()  # pragma: no cover



