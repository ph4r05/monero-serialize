#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import base64
import unittest
import pkg_resources

import asyncio
import aiounittest

from .test_data import XmrTestData
from .. import xmrserialize as x
from .. import xmrtypes as xmr


__author__ = 'dusanklinec'


class XmrTypesBaseTest(aiounittest.AsyncTestCase):
    """Simple tests"""

    def __init__(self, *args, **kwargs):
        super(XmrTypesBaseTest, self).__init__(*args, **kwargs)
        self.test_data = XmrTestData()

    def setUp(self):
        self.test_data.reset()

    async def test_simple_msg(self):
        """
        TxinGen
        :return:
        """
        msg = xmr.TxinGen(height=42)

        writer = x.MemoryReaderWriter()
        await x.dump_message(writer, msg)

        test_deser = await x.load_message(x.MemoryReaderWriter(writer.buffer), xmr.TxinGen)
        self.assertEqual(msg.height, test_deser.height)

    async def test_simple_msg_into(self):
        """
        TxinGen
        :return:
        """
        msg = xmr.TxinGen(height=42)

        writer = x.MemoryReaderWriter()
        await x.dump_message(writer, msg)

        msg2 = xmr.TxinGen()
        test_deser = await x.load_message(x.MemoryReaderWriter(writer.buffer), xmr.TxinGen, msg=msg2)
        self.assertEqual(msg.height, test_deser.height)
        self.assertEqual(msg.height, msg2.height)
        self.assertEqual(msg2, test_deser)

    async def test_ecpoint(self):
        """
        Ec point
        :return:
        """
        ec_data = bytearray(range(32))
        writer = x.MemoryReaderWriter()

        await x.dump_blob(writer, ec_data, xmr.ECPoint)
        self.assertTrue(len(writer.buffer), xmr.ECPoint.SIZE)

        test_deser = await x.load_blob(x.MemoryReaderWriter(writer.buffer), xmr.ECPoint)
        self.assertEqual(ec_data, test_deser)

    async def test_ecpoint_obj(self):
        """
        EC point into
        :return:
        """
        ec_data = bytearray(range(32))
        ec_point = xmr.ECPoint(ec_data)
        writer = x.MemoryReaderWriter()

        await x.dump_blob(writer, ec_point, xmr.ECPoint)
        self.assertTrue(len(writer.buffer), xmr.ECPoint.SIZE)

        ec_point2 = xmr.ECPoint()
        test_deser = await x.load_blob(x.MemoryReaderWriter(writer.buffer), xmr.ECPoint, elem=ec_point2)

        self.assertEqual(ec_data, ec_point2.data)
        self.assertEqual(ec_point, ec_point2)

    async def test_txin_to_key(self):
        """
        TxinToKey
        :return:
        """
        msg = xmr.TxinToKey(amount=123, key_offsets=[1, 2, 3, 2**76], k_image=bytearray(range(32)))

        writer = x.MemoryReaderWriter()
        await x.dump_message(writer, msg)

        test_deser = await x.load_message(x.MemoryReaderWriter(writer.buffer), xmr.TxinToKey)
        self.assertEqual(msg.amount, test_deser.amount)
        self.assertEqual(msg, test_deser)

    async def test_txin_variant(self):
        """
        TxInV
        :return:
        """
        msg1 = xmr.TxinToKey(amount=123, key_offsets=[1, 2, 3, 2**76], k_image=bytearray(range(32)))
        msg = xmr.TxInV(txin_to_key=msg1)

        writer = x.MemoryReaderWriter()
        await x.dump_variant(writer, msg)

        test_deser = await x.load_variant(x.MemoryReaderWriter(writer.buffer), xmr.TxInV, wrapped=True)
        self.assertEqual(test_deser.__class__, xmr.TxInV)
        self.assertEqual(msg, test_deser)
        self.assertEqual(msg.variant_elem, test_deser.variant_elem)
        self.assertEqual(msg.variant_elem_type, test_deser.variant_elem_type)

    async def test_tx_prefix(self):
        """
        TransactionPrefix
        :return:
        """
        msg = self.test_data.gen_transaction_prefix()

        writer = x.MemoryReaderWriter()
        await x.dump_message(writer, msg)

        test_deser = await x.load_message(x.MemoryReaderWriter(writer.buffer), xmr.TransactionPrefix)
        self.assertEqual(test_deser.__class__, xmr.TransactionPrefix)
        self.assertEqual(test_deser.version, msg.version)
        self.assertEqual(test_deser.unlock_time, msg.unlock_time)
        self.assertEqual(len(test_deser.vin), len(msg.vin))
        self.assertEqual(len(test_deser.vout), len(msg.vout))
        self.assertEqual(len(test_deser.extra), len(msg.extra))
        self.assertEqual(test_deser.extra, msg.extra)
        self.assertListEqual(test_deser.vin, msg.vin)
        self.assertListEqual(test_deser.vout, msg.vout)
        self.assertEqual(test_deser, msg)

    async def test_boro_sig(self):
        """
        BoroSig
        :return:
        """
        msg = self.test_data.gen_borosig()

        writer = x.MemoryReaderWriter()
        await x.dump_message(writer, msg)

        test_deser = await x.load_message(x.MemoryReaderWriter(writer.buffer), xmr.BoroSig)
        self.assertEqual(msg, test_deser)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover


