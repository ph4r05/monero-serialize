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

    async def test_tuple(self):
        """
        Simple tuple type
        :return:
        """
        out_entry = [123, xmr.CtKey(dest=self.test_data.generate_ec_key(), mask=self.test_data.generate_ec_key())]
        writer = x.MemoryReaderWriter()

        await x.dump_tuple(writer, out_entry, xmr.OutputEntry)
        test_deser = await x.load_tuple(x.MemoryReaderWriter(writer.buffer), xmr.OutputEntry)

        self.assertEqual(out_entry, test_deser)

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

    async def test_transaction_prefix(self):
        """

        :return:
        """
        tsx_hex = b'013D01FF010680A0DB5002A9243CF5459DE5114E6A1AC08F9180C9F40A3CF9880778878104E9FEA578B6A780A8D6B90702AFEBACD6A4456AF979CCBE08D37A9A670BA421B5E39AB2968DF4219DD086018B8088ACA3CF020251748BADE758D1DD65A867FA3CEDD4878485BBC8307F905E3090A030290672798090CAD2C60E020C823CCBD4AB1A1F9240844400D72CDC8B498B3181B182B0B54A405B695406A680E08D84DDCB01022A9A926097548A723863923FBFEA4913B1134B2E4AE54946268DDA99564B5D8280C0CAF384A30202A868709A8BB91734AD3EBAC127638E018139E375C1987E01CCC2A8B04427727E2101F74BF5FB3DA064F48090D9B6705E598925313875B2B4F2A50EB0517264B0721C'
        tsx_bin = base64.b16decode(tsx_hex, True)
        reader = x.MemoryReaderWriter(bytearray(tsx_bin))
        test_deser = await x.load_message(reader, xmr.TransactionPrefix)
        self.assertIsNotNone(test_deser)
        self.assertEqual(len(reader.buffer), 0)  # no data left to read
        self.assertEqual(len(test_deser.extra), 33)
        self.assertEqual(test_deser.extra[0], 1)
        self.assertEqual(test_deser.extra[32], 28)
        self.assertEqual(test_deser.unlock_time, 61)
        self.assertEqual(test_deser.version, 1)
        self.assertEqual(len(test_deser.vin), 1)
        self.assertEqual(len(test_deser.vout), 6)
        self.assertEqual(test_deser.vin[0].height, 1)
        self.assertEqual(test_deser.vout[0].amount, 169267200)
        self.assertEqual(len(test_deser.vout[0].target.key), 32)
        self.assertEqual(test_deser.vout[1].amount, 2000000000)
        self.assertEqual(len(test_deser.vout[1].target.key), 32)
        self.assertEqual(test_deser.vout[5].amount, 10000000000000)
        self.assertEqual(len(test_deser.vout[5].target.key), 32)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover


