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

    async def test_unsigned_transaction(self):
        """
        Unsigned transaction serialized
        :return:
        """
        tsx_hex = b'010203020051748bade758d1dd65a867fa3cedd4878485bbc8307f905e3090a03029067279b747fc01c6f0c749673a2910250c2e23cb38274d63b42f521b846356e413618f022d3d93ab2a6f3d2152093d606e9f79124179a50cfd02f750ee14042bf6060adf0cb747fc01c6f0c749673a2910250c2e23cb38274d63b42f521b846356e413618f0271c8b98b0c155227f372952915ee2eeadbac2e2ddb4d3711968eea2eeaef97888db747fc01c6f0c749673a2910250c2e23cb38274d63b42f521b846356e413618f0000000000000000f74bf5fb3da064f48090d9b6705e598925313875b2b4f2a50eb0517264b0721c00020000000000000000046bf4140000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030205dc02a207a1a45548f0221d43dfdfc09219a998e9280d5f765f889f3bee8547a459a03a3153a994d72327e4d92421d3e3291b1fa1b240de44b92d7f62ec0128f10254bf0769c5bf1ff5cd6115e583547488a3083a30d7c6a69dc886e231c4f217c8e259a03a3153a994d72327e4d92421d3e3291b1fa1b240de44b92d7f62ec0128f1027a10477cfab267414969c62bb5e8b15d8e78f08841680732a7ea37d5430401e9fb59a03a3153a994d72327e4d92421d3e3291b1fa1b240de44b92d7f62ec0128f10000000000000000108eed0b0917bf7196b56b2ed1f6f0ecba1e985237172a58355885360596fa6e000400000000000000007083d05d060000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000080fce7dad75d5a10cca900ee47a7f412cd661b29f5ab356d6a1951884593bb170b5ec8b6f2e83b1da411527d062c9fedeb2dad669f2f5585a00a88462b8c95c809a630e5734c000280e4efdef36f2ec1035565f1918b8c4740d4e5431ddcf50a670ab51984c78d9c0afff5a46a0df51121f7d68317c2b1b2d0f7ded72e106908cfbc5c0333f07dda1a716385c6590080fce7dad75d5a10cca900ee47a7f412cd661b29f5ab356d6a1951884593bb170b5ec8b6f2e83b1da411527d062c9fedeb2dad669f2f5585a00a88462b8c95c809a630e5734c0002020000000000000022000000000000002c01ca28ee97bd9754a3729285c0a5957c5ecf75f0cd0e182dea1ec1f9c93ae912c7020901deadc0dedeadc0d10000000000000000010180e4efdef36f2ec1035565f1918b8c4740d4e5431ddcf50a670ab51984c78d9c0afff5a46a0df51121f7d68317c2b1b2d0f7ded72e106908cfbc5c0333f07dda1a716385c65900000000000100240100000000000000013d01ff010680a0db5002a9243cf5459de5114e6a1ac08f9180c9f40a3cf9880778878104e9fea578b6a780a8d6b90702afebacd6a4456af979ccbe08d37a9a670ba421b5e39ab2968df4219dd086018b8088aca3cf020251748bade758d1dd65a867fa3cedd4878485bbc8307f905e3090a030290672798090cad2c60e020c823ccbd4ab1a1f9240844400d72cdc8b498b3181b182b0b54a405b695406a680e08d84ddcb01022a9a926097548a723863923fbfea4913b1134b2e4ae54946268dda99564b5d8280c0caf384a30202a868709a8bb91734ad3ebac127638e018139e375c1987e01ccc2a8b04427727e2101f74bf5fb3da064f48090d9b6705e598925313875b2b4f2a50eb0517264b0721ca69c0aa3ff81e092a2255096fd1a61d8fbe5cbb38edb42d0a55aa9263194d7b2000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000d0160a000000000000000000000000000000000000000000000000000100000000000000013d01ff010680a0db5002a9243cf5459de5114e6a1ac08f9180c9f40a3cf9880778878104e9fea578b6a780a8d6b90702afebacd6a4456af979ccbe08d37a9a670ba421b5e39ab2968df4219dd086018b8088aca3cf020251748bade758d1dd65a867fa3cedd4878485bbc8307f905e3090a030290672798090cad2c60e020c823ccbd4ab1a1f9240844400d72cdc8b498b3181b182b0b54a405b695406a680e08d84ddcb01022a9a926097548a723863923fbfea4913b1134b2e4ae54946268dda99564b5d8280c0caf384a30202a868709a8bb91734ad3ebac127638e018139e375c1987e01ccc2a8b04427727e2101f74bf5fb3da064f48090d9b6705e598925313875b2b4f2a50eb0517264b0721ca69c0aa3ff81e092a2255096fd1a61d8fbe5cbb38edb42d0a55aa9263194d7b2010000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000943577000000000000000000000000000000000000000000000000000100000000000000013d01ff010680a0db5002a9243cf5459de5114e6a1ac08f9180c9f40a3cf9880778878104e9fea578b6a780a8d6b90702afebacd6a4456af979ccbe08d37a9a670ba421b5e39ab2968df4219dd086018b8088aca3cf020251748bade758d1dd65a867fa3cedd4878485bbc8307f905e3090a030290672798090cad2c60e020c823ccbd4ab1a1f9240844400d72cdc8b498b3181b182b0b54a405b695406a680e08d84ddcb01022a9a926097548a723863923fbfea4913b1134b2e4ae54946268dda99564b5d8280c0caf384a30202a868709a8bb91734ad3ebac127638e018139e375c1987e01ccc2a8b04427727e2101f74bf5fb3da064f48090d9b6705e598925313875b2b4f2a50eb0517264b0721ca69c0aa3ff81e092a2255096fd1a61d8fbe5cbb38edb42d0a55aa9263194d7b2020000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000046bf4140000000000000000000000000000000000000000000000000100000000000000013d01ff010680a0db5002a9243cf5459de5114e6a1ac08f9180c9f40a3cf9880778878104e9fea578b6a780a8d6b90702afebacd6a4456af979ccbe08d37a9a670ba421b5e39ab2968df4219dd086018b8088aca3cf020251748bade758d1dd65a867fa3cedd4878485bbc8307f905e3090a030290672798090cad2c60e020c823ccbd4ab1a1f9240844400d72cdc8b498b3181b182b0b54a405b695406a680e08d84ddcb01022a9a926097548a723863923fbfea4913b1134b2e4ae54946268dda99564b5d8280c0caf384a30202a868709a8bb91734ad3ebac127638e018139e375c1987e01ccc2a8b04427727e2101f74bf5fb3da064f48090d9b6705e598925313875b2b4f2a50eb0517264b0721ca69c0aa3ff81e092a2255096fd1a61d8fbe5cbb38edb42d0a55aa9263194d7b203000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000088526a740000000000000000000000000000000000000000000000000100000000000000013d01ff010680a0db5002a9243cf5459de5114e6a1ac08f9180c9f40a3cf9880778878104e9fea578b6a780a8d6b90702afebacd6a4456af979ccbe08d37a9a670ba421b5e39ab2968df4219dd086018b8088aca3cf020251748bade758d1dd65a867fa3cedd4878485bbc8307f905e3090a030290672798090cad2c60e020c823ccbd4ab1a1f9240844400d72cdc8b498b3181b182b0b54a405b695406a680e08d84ddcb01022a9a926097548a723863923fbfea4913b1134b2e4ae54946268dda99564b5d8280c0caf384a30202a868709a8bb91734ad3ebac127638e018139e375c1987e01ccc2a8b04427727e2101f74bf5fb3da064f48090d9b6705e598925313875b2b4f2a50eb0517264b0721ca69c0aa3ff81e092a2255096fd1a61d8fbe5cbb38edb42d0a55aa9263194d7b20400000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000007083d05d0600000000000000000000000000000000000000000000000100000000000000013d01ff010680a0db5002a9243cf5459de5114e6a1ac08f9180c9f40a3cf9880778878104e9fea578b6a780a8d6b90702afebacd6a4456af979ccbe08d37a9a670ba421b5e39ab2968df4219dd086018b8088aca3cf020251748bade758d1dd65a867fa3cedd4878485bbc8307f905e3090a030290672798090cad2c60e020c823ccbd4ab1a1f9240844400d72cdc8b498b3181b182b0b54a405b695406a680e08d84ddcb01022a9a926097548a723863923fbfea4913b1134b2e4ae54946268dda99564b5d8280c0caf384a30202a868709a8bb91734ad3ebac127638e018139e375c1987e01ccc2a8b04427727e2101f74bf5fb3da064f48090d9b6705e598925313875b2b4f2a50eb0517264b0721ca69c0aa3ff81e092a2255096fd1a61d8fbe5cbb38edb42d0a55aa9263194d7b2050000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000a0724e180900000000000000000000000000000000000000000000000200000000000000013e01ff020690a0db4802c78d9fa401fa2ba940318e13274b1948680a56de3fffc899a8ef5326fcf5989f80a8d6b90702388b0ba7d3100efe8ca5b2786c22e4e97ee686480476f75b127828a3ede50fa58088aca3cf0202e2f852949312e616dd7903a6068f3ae1928eb56b649baf7120ff86004a3cdc3d8090cad2c60e026f645e8dbda7210c756a5df4afacf625eeb64376ac453985ce44d57d88de376880e08d84ddcb01024ad5c1fb311243ae77594c3f3b45cbefe5248ae5b4991ccda5bdb3e62b5a5eca80c0caf384a302020422dc829891ca44fce70e32766b127a4f762e94f37ae44417450daaf4196c6321014129d9d971cf0118bb3c3de6280c178509b0e71da77b137cc9ae6985eeba1d2815c166a8fb2bd8e2dea649603cbc481c41102d29755d7e340b0f4ff866b7e257000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000010d01609000000000000000000000000000000000000000000000000000200000000000000013e01ff020690a0db4802c78d9fa401fa2ba940318e13274b1948680a56de3fffc899a8ef5326fcf5989f80a8d6b90702388b0ba7d3100efe8ca5b2786c22e4e97ee686480476f75b127828a3ede50fa58088aca3cf0202e2f852949312e616dd7903a6068f3ae1928eb56b649baf7120ff86004a3cdc3d8090cad2c60e026f645e8dbda7210c756a5df4afacf625eeb64376ac453985ce44d57d88de376880e08d84ddcb01024ad5c1fb311243ae77594c3f3b45cbefe5248ae5b4991ccda5bdb3e62b5a5eca80c0caf384a302020422dc829891ca44fce70e32766b127a4f762e94f37ae44417450daaf4196c6321014129d9d971cf0118bb3c3de6280c178509b0e71da77b137cc9ae6985eeba1d2815c166a8fb2bd8e2dea649603cbc481c41102d29755d7e340b0f4ff866b7e257010000000000000001000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000943577000000000000000000000000000000000000000000000000000200000000000000013e01ff020690a0db4802c78d9fa401fa2ba940318e13274b1948680a56de3fffc899a8ef5326fcf5989f80a8d6b90702388b0ba7d3100efe8ca5b2786c22e4e97ee686480476f75b127828a3ede50fa58088aca3cf0202e2f852949312e616dd7903a6068f3ae1928eb56b649baf7120ff86004a3cdc3d8090cad2c60e026f645e8dbda7210c756a5df4afacf625eeb64376ac453985ce44d57d88de376880e08d84ddcb01024ad5c1fb311243ae77594c3f3b45cbefe5248ae5b4991ccda5bdb3e62b5a5eca80c0caf384a302020422dc829891ca44fce70e32766b127a4f762e94f37ae44417450daaf4196c6321014129d9d971cf0118bb3c3de6280c178509b0e71da77b137cc9ae6985eeba1d2815c166a8fb2bd8e2dea649603cbc481c41102d29755d7e340b0f4ff866b7e2570200000000000000010000000000000000000000000000000001000000
        tsx_bin = base64.b16decode(tsx_hex, True)
        reader = x.MemoryReaderWriter(bytearray(tsx_bin))
        test_deser = await x.load_message(reader, xmr.UnsignedTxSet)
        self.assertIsNotNone(test_deser)
        self.assertEqual(len(test_deser.txes), 1)
        self.assertEqual(len(test_deser.txes[0].sources), 2)
        self.assertEqual(test_deser.txes[0].change_dts.amount, 3219000000000)
        self.assertEqual(len(test_deser.txes[0].dests), 1)
        self.assertEqual(test_deser.txes[0].dests[0].amount, 3845000000000)
        self.assertEqual(len(test_deser.transfers), 36)
        self.assertEqual(test_deser.transfers[0].m_block_height, 1)
        self.assertEqual(test_deser.transfers[0].m_tx.unlock_time, 61)
        self.assertEqual(test_deser.transfers[0].m_amount, 169267200)
        self.assertEqual(test_deser.transfers[0].m_subaddr_index.major, 0)
        self.assertEqual(test_deser.transfers[0].m_subaddr_index.minor, 0)
        self.assertEqual(test_deser.transfers[35].m_block_height, 6)
        self.assertEqual(test_deser.transfers[35].m_amount, 10000000000000)
        self.assertEqual(test_deser.transfers[35].m_subaddr_index.major, 0)
        self.assertEqual(test_deser.transfers[35].m_subaddr_index.minor, 0)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover


