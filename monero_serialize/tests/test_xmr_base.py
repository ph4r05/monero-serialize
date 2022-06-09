#!/usr/bin/env python
# -*- coding: utf-8 -*-
import binascii
import base64
import os
import pkg_resources
import unittest

import asyncio
import aiounittest

from .test_data import XmrTestData
from .. import xmrserialize as x
from .. import xmrtypes as xmr
from ..core.readwriter import MemoryReaderWriter


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
        ar1 = x.Archive(writer, True)
        await ar1.message(msg)

        ar2 = x.Archive(MemoryReaderWriter(writer.get_buffer()), False)
        test_deser = await ar2.message(None, msg_type=xmr.TxinGen)
        self.assertEqual(msg.height, test_deser.height)

    async def test_simple_msg_into(self):
        """
        TxinGen
        :return:
        """
        msg = xmr.TxinGen(height=42)

        writer = MemoryReaderWriter()
        ar1 = x.Archive(writer, True)
        await ar1.message(msg)

        msg2 = xmr.TxinGen()
        ar2 = x.Archive(MemoryReaderWriter(writer.get_buffer()), False)
        test_deser = await ar2.message(msg2, xmr.TxinGen)
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
        self.assertTrue(len(writer.get_buffer()), xmr.ECPoint.SIZE)

        test_deser = await x.load_blob(x.MemoryReaderWriter(writer.get_buffer()), xmr.ECPoint)
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
        self.assertTrue(len(writer.get_buffer()), xmr.ECPoint.SIZE)

        ec_point2 = xmr.ECPoint()
        test_deser = await x.load_blob(x.MemoryReaderWriter(writer.get_buffer()), xmr.ECPoint, elem=ec_point2)

        self.assertEqual(ec_data, ec_point2.data)
        self.assertEqual(ec_point, ec_point2)

    async def test_tuple(self):
        """
        Simple tuple type
        :return:
        """
        out_entry = [
            123,
            xmr.CtKey(dest=self.test_data.generate_ec_key(), mask=self.test_data.generate_ec_key()),
        ]
        writer = MemoryReaderWriter()
        ar1 = x.Archive(writer, True)

        await ar1.tuple(out_entry, xmr.OutputEntry)
        ar2 = x.Archive(MemoryReaderWriter(writer.get_buffer()), False)
        test_deser = await ar2.tuple(None, xmr.OutputEntry)

        self.assertEqual(out_entry, test_deser)

        self.assertEqual(out_entry, test_deser)

    async def test_txin_to_key(self):
        """
        TxinToKey
        :return:
        """
        msg = xmr.TxinToKey(
            amount=123, key_offsets=[1, 2, 3, 2 ** 76], k_image=bytearray(range(32))
        )

        writer = MemoryReaderWriter()
        ar1 = x.Archive(writer, True)
        await ar1.message(msg)

        ar2 = x.Archive(MemoryReaderWriter(writer.get_buffer()), False)
        test_deser = await ar2.message(None, xmr.TxinToKey)
        self.assertEqual(msg.amount, test_deser.amount)
        self.assertEqual(msg, test_deser)

    async def test_txin_variant(self):
        """
        TxInV
        :return:
        """
        msg1 = xmr.TxinToKey(
            amount=123, key_offsets=[1, 2, 3, 2 ** 76], k_image=bytearray(range(32))
        )
        msg = xmr.TxInV()
        msg.set_variant("txin_to_key", msg1)

        writer = MemoryReaderWriter()
        ar1 = x.Archive(writer, True)
        await ar1.variant(msg)

        ar2 = x.Archive(MemoryReaderWriter(writer.get_buffer()), False)
        test_deser = await ar2.variant(None, xmr.TxInV, wrapped=True)
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

        writer = MemoryReaderWriter()
        ar1 = x.Archive(writer, True, xmr.hf_versions(9))
        await ar1.message(msg)

        ar2 = x.Archive(MemoryReaderWriter(writer.get_buffer()), False, xmr.hf_versions(9))
        test_deser = await ar2.message(None, xmr.TransactionPrefix)
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

        writer = MemoryReaderWriter()
        ar1 = x.Archive(writer, True, xmr.hf_versions(9))
        await ar1.message(msg)

        ar2 = x.Archive(MemoryReaderWriter(writer.get_buffer()), False, xmr.hf_versions(9))
        test_deser = await ar2.message(None, xmr.BoroSig)
        self.assertEqual(msg, test_deser)

    async def test_transaction_prefix(self):
        """

        :return:
        """
        tsx_hex = b'013D01FF010680A0DB5002A9243CF5459DE5114E6A1AC08F9180C9F40A3CF9880778878104E9FEA578B6A780A8D6B90702AFEBACD6A4456AF979CCBE08D37A9A670BA421B5E39AB2968DF4219DD086018B8088ACA3CF020251748BADE758D1DD65A867FA3CEDD4878485BBC8307F905E3090A030290672798090CAD2C60E020C823CCBD4AB1A1F9240844400D72CDC8B498B3181B182B0B54A405B695406A680E08D84DDCB01022A9A926097548A723863923FBFEA4913B1134B2E4AE54946268DDA99564B5D8280C0CAF384A30202A868709A8BB91734AD3EBAC127638E018139E375C1987E01CCC2A8B04427727E2101F74BF5FB3DA064F48090D9B6705E598925313875B2B4F2A50EB0517264B0721C'
        tsx_bin = base64.b16decode(tsx_hex, True)
        reader = x.MemoryReaderWriter(bytearray(tsx_bin))
        ar1 = x.Archive(reader, False, xmr.hf_versions(9))

        test_deser = await ar1.message(None, xmr.TransactionPrefix)
        self.assertIsNotNone(test_deser)
        self.assertEqual(len(reader.get_buffer()), 0)  # no data left to read
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

    async def test_transaction(self):
        """

        :return:
        """
        tsx_hex = b'020002028088aca3cf0203002d4401000000000000000000000000000000000000000000000000000000000000000280e08d84ddcb0103054f260100000000000000000000000000000000000000000000000000000000000000020002f19f9fdbb490ee5a1568723c33ff1fba8cf08376e134b0ea3835478012fb3a35000208d4343dfa3a42aa9166534580960054372bc45701dffa0f9bcd2b9083f6bb2d2c020901e38a3cc24e1f88d001ca28ee97bd9754a3729285c0a5957c5ecf75f0cd0e182dea1ec1f9c93ae912c7028088e2ed60a1baf8383ceedd2b78f5b332c7028e0e8152337b072357ce2d95d18e9238535be5ee344ab24faea09a8f477c06efc5c08c20f3d60a954bd9e5f5a7dbc354ccf8f65dc3df1dade64b63548d0d6d83613f3b88fc1baab1c6b9a6e1d7e01aa814096adfc8b9a4de7e0f5f4d0452dd1125d81c8275ba13aa3a3a835518f54927f30785317238c3b75878b36d6b1dff190c7dffeb1f074fdb907e7524eed818feaa0a887ff34caa3e642bec9d3afa3119317f777579bb4cd040fc97e289771ce8f50f8fba4cb6ba2b01b198b12902b7bfcf21ac9aea38fbe339e8edd1304225ab5246fd5a70dc4eb1fd8f024a74f898b7918cee43bb11ec8b04601a5e9911636ac843820bf70806911ab43e0d7992ea133ac210bc5938eaeebb32fa1c329200cd85035d60c4f33531f8ce1e6f5ec4d47010d5d3e20ec182b46b73085844b4647fea0567c488aa13d40d2dacba0c19722f72fd95b1bc25abc2ac49c86afe1f44f9b6097de69ebb233b281d2b179d996978bef22d6dc78d28c3387b408e05377fb04408a37c58242d76be9744644daec79fbde061270daddddb90c6b402acac5bdfa20cfd0e9b2dba45fbefdd69b21faf9a7b3a881a1f9c9192b56955478e5283c84b0f79372237ef625834c30c201f262fab1ca7b9fc9d318c48a5b8ceaea72e368d0e4698ae7afdaa8f7c378d10e4a03d3e7a537a3fb124c6475e9243459bd324f50338a687df2145d66b06b17b65ee2ba8f10d2ec7979861da631f30ea9173bb5c026cde11db1fb80392c4ab7cc931dd1481fc01a5b5eb1392aef09129044ae0fd07e0c9809253f28313add1179522295ef79a40dceaf451d1d08d31d9b4ee1569012cdde41c22a366e5f050e1d681c9170f7db2ae75ada97fe616c8fdca87a8870b453a4fd890cb3239ce9a062fcbe581be441ff4f74e8274e6e4dbcd6690a16206c1f7b37504431b6fb2f735f27cea48d01e43c49dee981a7cf42f588c0602170bffb708ea53623db7e6933c4cad16ca6128f3428d1bf9805524a527c58d07460c9c4b72baae042711d8cef73f64aef86d3c82afefef2501c27bab52967fb1b40580a1673a80bdb2f4da4eeb0fa4100ffea36ab27041e8f3fd71007a9251ffb40eedfbc95a1b592901a607d78f8ed8f3d441558755ff7509f6ab5976d5282baf076b60f59b177fc27fa848dd25e76f457f8410b7706ba713da6fcd469db958e1012dcc5532598f7fe27e68b847e6998618c0a1aea7a2f73194e31b1564e4cdf80b3b0ce6a996034502526d1bb6b847edf19a681ad65d0eac545fda8871cf34ea0851e8db3f9c1fcd7711a9f47852d757dd7cdf941ff56ec12a6cf01a409ae53f03ab5d9ac409d44c26a56eb3aee8c889ac11ad360296dfa2626c141e4f099a4f09258b5fa5ed07fb0dcb82257c9ef28ba772a86bbb8eede9292cc828ba4478ea0f444113413038135ca1e866847c83acf9b898cb7bc0e43851940223cb2308bf065e87d7b835a57b16e7ba4d16f9308e6503a18e3816a7c1d3086ad31eafc7b70bdb5191f235cb2a18de0442518587667fe693c14c46725835b6aadbbcaa9eb90c7d28d76ef3f76a417cfc0337d40d0748251accdb0f837c401a03c9dacd5bb40cb792cf3895f106a256b5c9491d758fe35139ebf0adc2e2aa95232acf113d440877c7962501dc4065dab2307042411f7c3e5e24d8895c700389289f5757c34d09eea055ed488ebeb915bd3e6964159fc3f64c64459113e10dc0158f0c3c227107910b3d9c954b57cc9dc6ce38359da65ce35149610ee3dc8fa9f2f6e75042870b82d969cd0eadb4ee9ee552830ce863b93d566bff22f14fe1df4f9f2049782c0b60a7f326d15a78bfe345e8304d9e26070c81111be5b7da07ca1c9054eb7c3e048fc18f135c0121b62f057ef49ad593627501ca5102984f2d79b0e31f4b9849000e30441476b8eb6c7987a3bb9740a1951284206c71d8bf49b78d7753496a2601ebf89cf382c55803a2bb002905d6c90b049bb55f66ddc907b8aab40c1111e50199de696b600a3def533a9ec848523048ddf214cb7fb04f04f74525c935673a0ed87bbedb0923c6ffae8c46501d7b30f6f124e45063dda2f9fcec455423712a037f3b78516efeee2f541c27bf7787267e00513c630547fe7a89d179b6ab87ca097491b0fa74c93e5a2bd9ef567f5adc04f93937c53c78c0d9b3a759bc4a158a0e683e0a58d50e008e40e57e63e024e516365604df2b85b8ab4fbce39c1f46e309292a985f7d88f0bc4c3c9032e0a7ac50aeb5ab732400d03500a6b8c1a85aac0e6f56783e70106a0c85194445695d393b30fde6faa3961b273285ab602699cd0f5262063f116942fae636a0a408737fa7e9ad7bb0ec06977c9f29b98f5d2d9b06bcf3ce53948ff90648c7913baddaf500d207f048f90e8902ff436ee215f5a00232b88d6360a5bb20e97befb1074cac6ffe017ca61c4979ab0fff29a9100dea08ee27d3ba14e23fcd1e40d61ad8a98e580294acdc173823d3c93a0361327dee09d1cc5cd3a7dbbe30efd637226c15845bb808a024482856dc09902ee0268b5a02794a69931dd5e0abbeb44f11aa8888ff944b183732aea3923c9354b54aa7f10f49f058ed5a510f94f874f0245c971f1045324342e811f21cdaef622d62142306404f89e666d1f9069e7163fd1155973eeb046afbb3407f9ffe129238873b3f01f51c2053e5b1a31a242f95c82ff5e78044bab8bde495e4ba735a4f211df8db05154eef62d00e7b0b637c3d99e647861125057037e66420da2b10e3f390908207630bdf4eb0f27c9b2afb171153512d80eca7fdaaeb6e3e891ee4ca1359f4900a1a683894ba4fbf6b5ec260cd1fd6d4a3e327b393b1ece780556acb40ebae1309a0ed1468795ff08eb5c6e537d916b7e239aec9d97da94f57f186ae7dec072707f6d3141e331f233b2fe843807cd12afafb3a89f5f08c661756b563e45801610850db4503a8d009c4f61418efe290c418e5587f1fde280dc6a51159a5284f8e0c362b622cfe87274dff821ca0af0b47fb70fdf06092e27e093a56043df06ae30235ec1e1b7f34a015e1d516b5fd04b227954b57b0a0f8d15d912f885edcbe3f046c14a1caea3a107414a694643f1317e09d962b9bd240b2712ee20071a8b6e204e9b9a00a51e4f6e6d589c1de6e8c1d0f2118ca39180b575526b5c433dcb818013858e14e93470fe8442b118b91d9b6848fb0180c639604cc7b4c59360770730b77316ce36880d9eaab14fc1f17c2e983b42c22d4b239fdf7d4fb5989ae2d370c59a8c950a223bb27bef53a5ad40aba22a527033738adbf321b9398f195aaf006bfcc93ad433db3366ebc471a9bd5ab4aa5834c81045d3c4f60e409630cf3a4031aab6b9aa660f00db6276c1e597562e4472313db36dcd75c235bcaf915e6b800dbcf94763c4036c48e1ed55a852f433ae540a49692af8bad8e0e96fe2120bd0a9d6afb690800f02a3f67e52c137d62fa587892aff692d409633a4b67ffb0ef09af578da08f506a22fcf0b5a28a0097bfc47a7d5aeb9234d6ff20f9c5e330f405f655d9a0bc07f4e378d4625258e4a4c01435bad36a8b258c6350f989b4bfc50f12173e649db71c04ee6afc50cf1381911daee6168958b49ae083834ff07a2d0b54a404d31da6a8b291502fc7819084ebdf31258e4e9bc1cfb430603a6a4ce90fd561210385861ba5ad5afd335149ccc46dcf4e2253c26505233199d1b47e5c07b1316fc862e31f749693ed483acfd44e3010ccfda3ed75f76b9e490c31866801957c883bea7c8e0a43ddd239fa022e575848954f6e97931429232ad25556500c0d2a8763c473947c08848d8d916f4bfae06af46441cab90910744913e44ad704d0f8ac05a828d48416d7d71a64ad8c854cbe183a0d3cb9cbdb1a21c0006d2904ccc4b8bdac4003c0aae63cda0f1b7fd6ec0eb95a42a0ae9af62db85a7de1e50fbe17c6913c327cdc6a043923e49bfc9738441b4781d18b721b273c50d81d58020b23dbb46f25b58f0c52e5d1de5a553ad7471793379927ad34137c5f0fd3d50ee1f4552f6487ca1f351f240190cf3d5d6e43a7a7aba9f0d42308459f5eb3c9036d3e81c281d04841df28b1a7494645eb2e065c52ae18c10411740b83357daa0864d17d8d8bb94c10b418791fced725c5b7b5b7ecaea18ecf9541803b25bc7b0ee8d21502ad5738141ab9ad86b7f6085332d829805cb2c6875b1227446621790e982a4f2b6860be1798b6af4f1791352041bbcb8268c010631d5eac702f3f8b065e9a0ac257c4037c7f19dfe6220fcebcf157b73a44f2ad0c1d6dbf1846fcd900faf66534c6f8837a60ac757d9fe33b64475bc0e2e20f74c66d62009cca4b130851f224dd98fe95dd8df1937c06f32619667267421a34c692f2459b8ae854820fc3cbdc3d93b13992c46c51b90cd42e5d2a68eae463a21a2fedaa6f0905c368018225497244f8587ad2c0e97722f7df8bdf147125c15575c283c31f68b59cbc0db055eb6559e8f833d1250f113f966a8b0acd5e5dfb3b332bea28f7bc22fc870cf9e17edccf775b9cfdab810f59c50e9bd3a2d2cb57b58282f010cdfe6c0ffb01945beaee7644fd9a3f13249e18d14341f0df4bb2fb6066064d0ae7d32fdd2b0876004534da7126e1ac5237218d4a0e2b30394b64f151187c412002313ddc160b67155961149a3e74bc30ecb5745095b6e170c29113fceaf6245c456b7ea3b90431ef985e2fdbae53d6041966f402eb3034d5ee3a4467f938108bcf862343fc08391554f9a4166831f483eb4bd3881901f01cd2439f950207f258b0da6139f30c6a1a677f52f09af08086cb2528ba0a4564fd8e25621bf71622bc8f6ac3672e0ae0225e52705b94dbd9f1e7d317fdb11495845d162bb941db42f8e9bbb610180eb90faf11f421da0ceace86fd1cb39f1b6955e5e74ddbf5b0acba0147070bc5002bbbb9c2ca9e509667ffbebc92cb61e6a73234d511f11bd4281b75cc3d74790dda92571d2c0c87dcfc91c8a226db9d57466e1df26b28d0625c6416b3a8a7320765ba9c9e9015ac86602330abb698df83f13b02c9074f9b4a9468e77698502006136af7df2c8a5c9c5cd05b8fdd5ca1c5478329dbdfd61f72fb1285305efc03034086fa93d29a9aa324a99f14e418bb19c28915328f76b4db37800b567e0aba0947ba147f9c40afb4a2b9ec286dc34da5401af7592c2a62ea8df67b3c77725c05b3b74230ec19cb1be8e12355760f017c401b366234e03e9571dbf7263fb0ee09e0e2de4192db6a9fe0c863efa8a777e45519212d79849f4447bb534ce39d140f74d1eb0def9276759f4488e007108981d19e8e17d97bea92eaa31812fb386f0f188d27ec02c7278940f374190a515d5eeb62eb76a4f7cd20cbda0d79312e860656e2bc071cc970412d4d387f9efa05eef3d967e97fbca2f4aaecf3c5d5d33401c70058c11bffe73a6f66771129b8830601e85e778a6ecbb2d3a8e756dac2a9067ce364f6503159b94ace7494fcdee6b29c91aca958f6149c47c583693ebba706a79452877de09e3762a5416d8c33df3d2d66b1870f77258d79657ca7f771f503a01bf7ac284269efc81b3f98189b72880bf2f8fb1297ad2d9047ba80eafb1f0a1ef95556cbc8102ab2ec52266d8079d0500d977a9ee886e0144b0c7269291f07d991cb5fa0b73c725c04cc6466728ca25fbd9cfab960ea7429dec482e2045501a4be7089f8812d50fdbc5de8aa076cf34e9e20f38539c6b3474521f3f6bc5106f2cd735f1cc33f4f489d3c170d713d9037fcb103e50da0a3154eb8887a89ed0a665c8886c44058922fe781d771e6db11b13d88646c4f6851a205e14e07e1610b468fdf3ede3d1c779801ac554b2a54f182d2b6b3937a08751c3ebc1a1ea6740256f392b253cb949f67283c537d636de4ba8c4d579eaeadd20885e1d87c3a000436d6ba9fc36774a93df2a39c74d30ba898ae4f9afc45e85f44caf0c6249aab037c5ae7afd958c733da69fedf195985196835c1b4de8a996f64a0da54561abc05c47ffac0efc6d42177293af85e2a07705f23dd2a04f363bf520f5ef1d2e7ea0461950b03da15b78592fffc0301330d9147bd59b2f737a679c31fdd6bd603360d189ea288f3ff9d651cb852f3f1a7c447cdcbb1c2fb42c802f23917513910dd077a39fc87022416f3d4c97bf0a9085dcd9c5cd8cc5f9a83d23ca86451bff2b4e364b98222ae68cd22cd7b87034450ecaa79e3a73d8a74b0615d49fb9f31edd725e250f57f8fc367e0d11486eb469afb7b14d40a035987ecc57f6e4e1004fad4d457bc86a30bb25c7b4d44f23bd564a47130f23ab5a4db6800fa8452925584859f010bbc8b9e8b1377f3edcb75e8878f26ef6e8c16b05f65373dc6bdf6f322fb34b3f377a7aed3909606fa6aef5ca023b63e4ae2d3a97f7e17e82408a862d42d0836ad8b86888a54cc21bfc56af2c72ad069cb67053757cad476497dcd3511bd4e74a87a6408b7d0fa3cac7164671e0a8c4b196c0c56a723443dba5581fe27a8c41ee6911a0f5e561d63607901e694be2ae92f06ce78ed2ef01e197c6eac262f2443f9395e9479cf98d5e92006113c684cdf2db63c38859b0a402c16371d9dcd0db67259d7b53c69d20b0407e63b28d1a67d76cbb547673323ebd9da1d5ebc0d4db2c02b1016afa23551ac1c872778f613104557917d7b95366ad727a767998cb95fc5fa4986ff465d48eba4bcccbb275c945758b084d5cc0eea7ac26a7b9b7895b8d818afb30aca4024c7f9ee2df5dd060295d6bdb1258074840bfcb37b4b0d21a35e5946b875fdd1e615ae17d72df36b321cb29e925206862fc55cb55984d2f4ebdf75819e70d54addbc1484736366eb7302ac7dda6794e3b0ab08187e9b8e8f8a02361f6da057da03243a5934027c5037400c7e8bd54b8dff171e4998a2370611f36e174614801d1d2fcc121bbbf3c553aff1845edde8c699e6ae9a22a9678b2492aadd00a804efb9ac2d609ada1dfa084831b6741f66da10bc66c016d311c38d85de72960b03da2e6e6787a3ac5ff83a5302895f02d07c701ccd8953fd668cff6910f9a43cb0a08330ad043fae162ca08715db62b91d3e028a282726a39f91b400379a337bab45db6b7a28928e4b3b7481aa933aba2e5742131512d0be310d21d17c3e6d893af3e034ba469146189aaaf3b8fa7c9515d85978d6aaeb98e8e50bb14d3eae3a13551cc84ae8f9082013ec85fc125d325989b3251fdf994daf23df67792f061ae21a7bf7370b9efc92f2b5b8fd1a11626754d4af49eec2ffc582f11df2edc73aac94da2372cd1a259aa504bfe4354855981ebca127ebb1e5420a6ec7cf49bf83e7045c960c7401d93b0087e97541743bda8a5823c8cc2e80e0dfd6d955b04286df7826c1c20de5e4496e162a3b98c34d2d8e3e8956481c1b36bc8cc7527e39d65b7257d2bda8fba51d8481c03d9649221c890e3ba3e9c1c8d4376fb8cec4f1e6ca641b2444b4db0ad209bb50af0552051ef55e986d77a043956e54f2857806f56b68cf1c64158e78cb6cc846eb0e6a4e0b8d10a9f3ebbad14a0c5399087349d477dff83ce65dc381131ba439296c473e5538217e0ae10f156a95d9ffc580e1f04bb3fb161d631ceb26cbbef4717f719ce01bbcdf0853a5b33f13c2b1d6788ba4b312d062c52baabab579754af3dcf3f2fabd0231f4657b950156ffcb994496e0da8a27f20f9caf612e6bc7325ae9bd20727f03167d41a1cc8ea13b09d445524e9c02094228986ca07349fffd11124c3a465a09b25a30f461c8b4097013beb2c4158266190534ea523cb3fb2d54f86e1a57050d2dc092b02b5952649a4a6799b887ce84bf403de133415db9f889be184955131ee9f4826b50889b5dc70e0e87b1a28a3d6086492e0a5468dae05963625432574576253333de3110793b4a69143b9a5ded4e38a519d3c8ea86fa4b8ce58907267e6ef95ab83179877a6287ff1f6cd52a9794bfe7afa23ae66c7d0b9fbaa22ded0a05ce2cfb1ae9b3b8817713dd53e2b5afed38953409e661042690fae3bc98beae59f9ad44f28452d26668d3808777eba15df9c865831c5404f22f4f38722f474ce8d159550d0d48339cd0eb08c866972b36372954bfcb682fcc818f03cbc193fdb4c0c5fc09d3eb8e98b8e0c71c41337b8a616c823433e296e4dde16c75f1a5d63da1d0c8a6f86b81d1865e1424aa2feaa9afe079fbbc762e6b9b438a9e7588aec58378ea9ef305cc234fe6627bd1368d01bbb8abf0cbc253f38b632ddb8004c76c65b5a7a800079833e324e53fc405b4717786f41479ee55854d9fdd66ccfc2478b228bb8521e32d204bd55cd8c6f6db5cb7bbb74760016d874edb09301bc6d4a5875149e232b0203b6c69784c1c14c5ee082a52e9796021ce3ef6e360e9b9af92c3db2733da094c5639d60015b11ee06c328c84dbfb36d639a9123f11ad9e22e6b282b0160f92b0c09fd520c4d2921de95f976b62aec948c559e6ab2142a1177cf1c3357f7eab82bf7ecdba4755ae70ac59928b4a70497a6dca95f995706705ddf6d1edfe6d9f1b57b4e3f995e5e72b73e98cb0fca3a6b3923849f82f012d677a2aac907a2854a21df24103dba13bbc81bf318e82299949db9bcbc61b505804c6eb9499d448f494619e6f01e0e188faecb4b35786ac0c6366b09467bccc648b438c097044e5c0292c2abf3271aa7b5f90af005208c884d84163fc08664235b7c892079b4de0f7441dd40ff8c8abeb4ac79ce5a0897bd639ab47871dff53f219dd75b39164c9a5dfc2321d851d5128b3260916f4fa45d42c2ae6b3c81755f8d7e6a2b7d3bc30878f18003d0a5daf1cae94a2286a0b7e218fcce8bbcafe6d8190fa2b896f7f8fd1f3456356d65e7842c5d836a839236d65e7b45ec3f684884385f07d1f7c3b1080285d809094eaa6a11e9c3f13e6b32fc4e364b037ef0f7f7786e0a3c4478873465a0ea542d2a0b65e91f876403ebc3e51bcd4569c8ae1157174f129f405026ab0c49fb16056ae348a50e0e85e1651fac280b6e9ec3c3cce131bfa3985e0a9af27d9e47c90175a4fc8844382b5bec56a004c6a696150c0c543a84d227a12b1ac0171167b853918be999b32805a95e2cffa2a4fd71d08a193eb6a684821087dab00438217ddfb9f2516613ce575dd192737fa7f2bbbba246e338eab72c3ca55ad0dc7d5f0d03d5c62c35a9614a605b2e28fae4fb9aa2a4c2da2db1068082b72d90a97ff635ef324ba28925ca7b9b44bd8d5661fc2fd46eb1f97cc07ade74127bd0bc744d036be6c7e35969c6dd37fe7437bbed5ab9f9d818b358ea8107ec1dfeb02b0243794450282ec332ad705e8b3e89db9225101ef6b30074b886cd49edfa80392503e79eb8a30934716d5a86e965d1b849c764cc84a44d3c643c1d678cbe40541f10ff5f87ce93baeb88f4c2fb2cb11ba895851c894937ec918c7bc3b64410bac08c449b831f870351a12801c0037415e09e66955a031c6abf856ac19b30c0f0c91777e93f12f7dec827e4cca1afc5639cc1def44faa3eb4d2f5d8c9aaa000f34b080326af907232e1ec4568086bb37970d3084dccf27ae9be54c6864991b09adfecc6805622ddc463147b2e32347a7b07779c58d4eb329828a7c59cd58f40cc1447b5ed40e0b81251f17934e0667e47ecd21e14a7d103e41f2959043c5450798deb5355c80cc9b2d35cc8d373fcbd1e80379e15c8100fe35a5721d2abdf60c3a9d048ae5031d61c0936789e7d090009e19ab9153cbb5c86d2c606946f2fe0674ccb026d3ced377bc18719bf3c4ffbdf3bd4eae3801268403138d1ea295e1008366e5d0db756c946dbbab129ea2874f5a57b1c2dab09e995a83bb52592b1505c96c34bd00e1a98a3d52b41890b0e03c73b16a1c47f19fe204c709ae1161250c23aba9be1685f8cbce9f939e77161cfeb62566b7520c416f890621180b9f9701e0a2df22a76962ea13997076ae8dcb3d09e9ef57aa57826404dc228b927f5409270528e2dcf478c003d9902341d684962f4ad32ad2777efbd28c35099cd00204f94b8e09c9db6c8bfec8c3b906b0fae0d8da9b3db85d649e8ce58e531141f205add4ff61d3cfde89e60c4561bd2ac3aa7be53a5c56d1c0f1a3d4086e40a4c501657e862fda9ff30ff866efb450d5e5a74821e037ad15be216436f92e9439430d12bb42ac33188e527781b1c88f9d3fc254847985306b07b7c7fde1303fc64f0615b241434362b5384f0994e2261ce7a14691d3d17595fa108dd98fac04db8f0166e11e6d0694d2384405bb93914090ffbc28c21dfd921c285a23bd6076765308704258bae4e91e8d5487fec7b4778d5a8207c991a4c141ae7073a0be76f3520de50c11f2ca186822fbba7b76eae8ecb52633b84675f36ec2c3639224dc51d309e4f7af68e33767266846900e388765c2dc772180aee4ef6654826582b93ad90c2190b47f5f114e94a4b35241329b46423583e5e0464d293d4d95155604e9220889a2e834a0b78807c4f06cba0fa2900b92392cc724c6a94576b19687a6d70903538815dbd3de11ab39cb792b0f1fc78629ffb34330a5bb259c440930d225a201e72cb93a2848b13fd154ebec28b0f75a0221c54823a5c3405e4514bff7248b01887fe5ca1bdd585974d6f7d2ec1e6675b7d2f886fa6d00d9bd47490a7416ce065768dff30e3af261736b508aae38cfe5beb53bf83acfbc68dd05dc931a305c0734f173b4f4784ec62b54ca97342148a9a48a274278a862cfc8d92062aa774a0bb8f35bcd5ec65125d8c4d76b31a447a3b31a75451111e04aaa89a1119a71c20893d1c9f2e5de30fb0b47c44195005c859d524f49e8a9b24a309b15a158053409db0baacd42bd7484307b0205f66d2d69fbb96d85db273fe8d0d8b5a89cd8eb0eb2318bb1c017a7bee59fee3f964f0f3df0ee923a41c9c543956c58df2be9030feefb2b220021394f52d8f20dd7a4c806409050c80a65d88fc116eed81ae0070e71b230ceb95e532a7eb8748b70523f2435e81eb26ba517d6c04fb64604584801d7762211fd4fd85f7beef9f841581e041d7c90523e08a5f1bb43d22e881f0606433700a09570a04a1422114bff7d6c961c635641a45ed3f20b877c28cb10e30560cdc663db3632f4d685a62250d60baf5697bdb3d0c362fe6488bdb27ae063076474e56ae79eba573ac2e0b727aec88d3ccd6ae2600c78a13c7395a4842a920ce6691537fb2fb3aa69f7bf9f1a32c986438acf418f2cb7ee9e87b0052bae7d0e62b0b26d9ad6fd40a87eff4252d484bc936016a10bb61da5ca62a908b560740da967f27a29f117e0fc2981ea6b092011c7595af49451355a098b9ac5d82df704387e6f68d9f047566ee8a8312079e8218946ecbd2083a8f0469daa4575e5420d29a2d1e796e5a5bd0aa124bbd152907e0cbf3a975ded6f83ff05e6c070168e038f8ae126982a9487ee392c04e79e2a5c9b96c2c2bcb97f937e3849d88fd04500e333cd7d4de4234cee2883a18abaccf7d2154fbc53e0c1f2976bf4ff8a9cce0276c85b6414b48af26e38d904f64ecfc78986f576847d4cfc6a07159af8232d05dde862274bc178447f1c663db422addaca06645da69eca8d01e5d2c3beca100547b3e7592ec5fdfa49b77cd56def7ed5706f370021947adbb1bb8b3da53c7a06c109e4ccdb7467f492b48a4a1bfe10a8cf0dc52c556f2897ea005412b68de60878f936c01b56e7ea8bc6fbcecfa6f3288df369af54dc29dcb401eece3be1da04c84f56671105077e7167396015f9c0f21c46ced1ef59fe6f599ec8de9f7e4a0789d2b87bc1d160229a9ecb5b25e658b46854f7f80cea18b317801ceb02d92004c7076b176a81982ebfeee0b7468c51f536faf2315727864e61c35c4764a4ea018f9d24432391d3094b0130a58f735f3ec36846fe976456464b5b016479c5d00b10683d4c9e2e421216c123ba526e4f2b51ed6ea415b1deec8b38ba09877c9b0d5b00f6f45428d59ac13afa004f5aa8ab5a5a6fa2dd20bde725030e8a65e43700ad271572a075d259b176e298b1113565ff0ee5a1bf8830b768abc3f50fca2f0170edfec0d8c6199249524d1e74c3a9a27591fb4c790cd4a5c1eaa6440ca8b40cffe5a304776c3f20b82dd3cb529d085f104a7650c01bb9cb4c9ba52b5027b10940904dd03338086571fd3605954c5cf493bf8da529f441b68762bd744f378d06fd6688bede99b7da478048ec59f3417dcee761c71c1786d33c0b25558183460337b2a97867167e820376316986c81852f6e6eae379d39ffe8eba6172ca4ed902a90a6479b167fef6215c0032cf948601b5b923713b55c7f8a98a3ac53ac7dc0f21e9b1f3d9563daa9f30b2010c94a1274e8defbfa1b6fa71aff80a34cd0a3d0deafb992836010ef3675a6e42ccc0178a82d7e8bf478397b71dd10a6a74bc5f0324a67a51f9bc45edda1c3324c7304e2a5bb5f97cd4331c3ad785a0dce23ab00f0ffd0571e01c06e289f9ac69c50d468227348b586c09bf57599b58f30340c00b22569fd70111dfd5854191e2f90a5019a0264c0c92ec4979f1a4d35f37ddcf0dac4198c1a44d927809b65e9879c7a415f26ddba29bae4a1a8349b0854763540e41a1d86ecec217720feb185c4c484d27ba92e1fb653161bad3a5bd213c9bf1062db28fedeec2a43ffdafa9ce9faf660aa96159eb2bdba835037f48536b941b0e0ef577864c37324b5c7a0255640fa27dd593b080adcf04f112acbfa5ad8435084473935043a3737e88e083f6ab128b3951a30014790c261db987546a62350e0149cf3f88eea904e0f928697a4daf66ca515ccc9d527d5300ec3626a13321a60f4178c28a0f3b5f962840689928ec31ca8c2cabb2b01f8314a2d185a4d0d9e007556308d8f344da0936e7523b17b68f7fdd3ecc4c3e2358028ce7773dafae520ddf32eabd43590a0e01594ab7a683002f2da88080fa39b38d8123c050b6ce8c0126f1fae6cfdc5856276f00dd1e84f82fcbf7df4040a4d057c038916611155a0db866ae4675a83afc0f7e5a11a1eccb64d5b7b0cc1c4ad03ae0a9a15eb9637807a7fecf6680b7c5686cdb06849cf3e445ffe3eba98a53374729394bf71ff457022d7b43d34100bdc385a2b112b50ee56dd38112021a5d4791aeb2efd78626090a2b90bbcc26096bf1490f20366c280bb7416f2e45e1714cc62f7fb14849a83c0aea84c5c4c315edff67c8b5871b767d89b7185a69e94f36f104e5f759904bba0559f6ec284d2e795e2edd42064fbcc6c3b2f4258f66b96822bd41eb20578c5503057a4df54b7ccfce85c59d9744da23120c93ecc7e9e3adb8f41322932d2717056bcaa5e69d35ca2d3d8ff84c48d425ae922c75e416ecc83d984b3e755273990284d5c62674227de7fad42d6913da3de532170c0e79b77f4ce2c3adef3c5b81054acd91a01451f483a24e84d24a18436088151dcf203cfb3d9d93723277dbe50a39ed03f2a4a0d232eb2aa752f9bef7beb9378f0035a5aa941d97a7927b3c610517cf9665ca5bfb6bcc50c668bdce39740b463cadc57768aa89a5c5c13ab8e80f1a0e0782a061f2ef46de2520b4dc7c26db6fa827a4dec5a7668c20fe530d770ccc28942fd05350a14c33c7e8effb5cfd4d9407a1d21f2290d983ad342055d601e695ba720e6e61b4242ba5d2c8827998c38ee888f7889a50c2cff744fd43a20faa5d4d49be1803c9beca63174b9c8e029ca29ca19342578a7570c4124635c90d05bff8de80f057db39e687a02ab38e1b0d6eff3eeb84b3c7434118f9706a8f0ca65a4a7bcc814016baa1a14807502fa2e5693e9aaa35f58de0c3ce21200b170f7ba771f6c687de02b953573b7ec9f971de49434979cfcf1c56f6c2e5f9cd7506fe4a5ee817c8e73bd14632799f6352aad0aef416241b6ea23b979e4549138808ab9d9263234f8dc477463504e672e2124601ead45eb74a9c29468197517b6e06fda3049f6451d1167b14e45585eeb8c8cca1990ffa9b93553c415755169bb70742f6f347e04cb952bcea8fca8be21b02159786d2222f22156752c586541f4d074b94d8f356381eff83d0a3e856d9c040582b38d52a3fd2887e1a62525fc1ea010ebc5f87f0783768c33ddc050161419913e529723ec3f7ad5865958e7b4f800b1ad30adc1b0c6f6c6ef8d8a420cdb3649ea93fdcd1d0ff10a625d32cf989b30730654580ceb36f6b9929488d957fc863a9d56cd96b5e3f20407c6ca5193e5d059f5fd14a81a81fd01f17f0c1a0096ead8a609c656c9b60bbc32788e8238fc30f28d310b581d120aa5151943dedceb8f636779fda68e74ebc17358dd0f503280679cdcb95a867db5b0f408ef5502779cd4bade1d3b165becf33cbdc556260970fc7768b9fae2e66e5dac4e396555b33d1cf9a50c55ba1cd9802bc315f2930920c16326976d9cfa47d261af4c9adc7d7550aa688efbe23851a19f019728e10110a64d6b90842e26df39d3427aefeedc8c1008fb70c24d7e3cee98b866c182f88057d50c28f1d1c93ceca38d3d943f34f9e8deade4ea6cc32802fad0355094940040cac826a9bcd240b88576f0c5607674ccc636769abe9192821d9591e1c45b70e34a1af9d722d6c270d7738d494088aa354e25ba9dd32db91f06c919ca55bec014708f224af3afca8d127ebf908f4f74d484431cfccfef32b6cb50a83a739a206bd1a8122abe4f7003c1c3c60e13586f8cbf4f54ded5f7485439dd8e6a81eee06fb5004c8b51688ff3db6b8f216cc02747e65b5e15c6b560d880387b42ebe4b015482e18b4a41008bf857189fde5d78e1585c919bd37b100e8c488a019d87d209e78badaf831aa31f05007b66d0680085afb1536c5731083716deed5b57d46204eb79a8c75db63c0ac133a15bdd01afb8f6e104788af43b1fb7e4a3a3612b72024e2315fe43f9d5c77758f86a927b19784c01897b563faac1fb4e92665aa786e0df248e715cca8b3a620e8a49b36d26329c484c0f99d3fbca372925a182e63958112e526cab4032ee7e1b833a677b483a4769602093f8e1a2d68c8c7dfdf7c0be02934066ccd3e204f82f6fb152fc5479758bcb6ae9d355f4bd1a8dd064a16b23b36f0ce2d3dcaa9e97118ce0f1a8bcb008b20e9a04489a9ac9f31b82a7c14823dfc4ab9916aeca716602b4bd0bb1fc03b04cd6f228c4662f8ef52139dbb43005bd0834dd910d2c0a85d7dcacec54068c0348596c47ca52c3b5ed6f80bc58f01f2a1d0aa9e40af65d1a6e0222ec12d0c098c0cf923f2b880e884045597a21018ee63d3e9773190042ec9db01687b114d939d3aa7e6bdefc8fad80f8a6fa715ab57336c915ed0727098abaf04b4956840c34e83f31a38809009a0ce2df91979f2a874bba9f09ca9ef7354fcce71facf8fe49607a182f83d8cbd06ca6e9b9e38c0fc0f630e955d6922286e84417d662e4d71748a1c59b44efebf3f791de276e5593c744fc6ad8b7ba5c523533dd8f7d413ef8731b90033d1a51cb185fad1908f9690e2099109125f14987826afacfe952b6567db33dea01ac10d4856984956d319c5c27d77b26e1be955d14112d1049e88e031fbdd1c6a262fdf5d39c466f6da0f591b9735c677531acbd2eb2e65d1e8a36bed9d853d78ad6d6cf0ca170e65500c1e3c16e3766d589d4c57e7fe29059734520ded0acc17b80fd232064d82fe3b7dfbbf3498a4ca1d7c9eb99dac1f19c2e3ecf738f8ffdf738b68fbcb9e84ea1ea8857998c40e24a693c766e41e93917bb9ab63efe1381ee2db5bfacb277d5376cd1dd9225d56af79a3969faaf9edf91b080c178d9c09ebe3297b6b52f6c7d1528d61163819dd427375897f5efaee3074d0a3288f93bbbc29347e5241f80c42a3fe0e20baf3beb488664a81768d108535836036d186028506750d65f361d7e10f6b13f3d8c27464fa5147e6a56f99376a794d3efe935b39ec48c3ad70fe9fefd95ebea1215ad75aaaa2bb449e6d3b957a77eb91d82d602444db931ad949d8fde07f19bd6f7ddb4643c14fd4c22d343af49b4ca3d92b0cb71f438d6c55c541a0a92f21cce569e2a59cc63c693adee884c2b373abcd3f2641b567f234f44b7c0dde313be9973d5579cba19d857cc2e6bc4caa17436ac666bfd77f67325caa762297f7036c5875ab62fdbcdf318d99cb29b7577093e2360ade2f7a16e8bd946cea6edee81dc0a8835e86fc288074f6a02b5e456c0ac943b7fb720147697bf7688cc7dd2f9733caf3e9a8430df781ce0ab51bfbcd89bee67d5d51526d95b72914bd696e918276796fa24c6af70180e84dccaf2d7478222ec1f9e649502b8e783da7b2fc997e4f424fab9ba0911da9be4341c9192cdf000ea272d198d4eeface456be924cc4a848ce197b94afeed6d519bcc1842f7fcda898323a791c588dc823d6e67c3cca9bd344d443d285729c205c8d9668e1b8adadce46fb7a06ea487abd2078d216c1ff3c88399d68704451184c6da2b97ae285a780ffab8ac0999d4c98308b1a8704be621a587823fb1f1c0bdcaaa6c01a53f4a66d6b361a39bbd63cbe5cea9c9bf0c1d9da08994b20d6f914efa8b2e2aadbdc156d889a78d4c1e5cc0dbd33b30332ebf63d23a06467c12d81f86043411a52bed3704e92fe825008dd693bf73dd2ff84fe8bfd3fc42b2ec88ce11622d1049f40ddd3cbec508d37dca53ea5f43e3840ef18797eb31e3cdc231c5c038cde840b48feb7c7aa058d91c027a09355c50b66b46f360c7c916c2c14b4d62517fdefa868a7d075748d4ea6d3cc5b6ad953fe533365bdcb6674268cd006304cda6683c7c979a28b3a28f6118c04294d66f08f1e08d06e4ec4d4a923adada631042d8385905e47526b4e551d441ea431b0efbe720bf2862489e65a9fc541af6c9036a0d9fad0c43f4d9cdca26bb4bc88822984fd8f8236aca384e7d61489cfdd3d2ef93a3e77c06b00e1f49c5ce2b17d95fcf06c1317ea3d2e79d7048c216faacb3ecd318460ced8726c274a81333575c903e19544e16209b9fe3d1e63fdbfd1cafa741490e7330fd83b7f6175bc95c31cd67ca0e970a1ee33a3fafedc811e449da05e256b437d1a8edab2b25f731169af331be11e5ab8e3b58abf866026ebbcb632ebb2227a710a6b2b5ee496fed713c2ba83947d8536604d74736da4bffa74fc6f02e6891d0ce7fae4000c052e5a9520eaa6ef68e08e4521c074ec99a2b4dadee50749496df37002a05b820eec702f94a58ab6ea65949a3fd58af6e9f12d18b2044bf9863b56cf9ebc514078c85572d2f8d13e57ffb235b546644399f0d1f3f42ad4194998c31b56758832ceae226e7f9764e84da03ca837cc7e9ba741e42a3687192633a362444a15a852f1fcc63d2808023a97cd7c4357c2868b39494b69229ddaf1db1247ab75c6ccf7bbcbb07a36daa8b89a5488197e0f16f3d6577bd45eaf8b841b7fcbf1e6f0530784fd2e0ed8d3e29e24a51348393c2bce7b968c5e67a3397d4379de5bb23d508c22271cb87d5ce0a232b2389f920b32a52398217629a16c01bfc626302acf08df8bccc725ea81a97e6cf5711a35ef9ad16d548888f62ac6631b8022656622802bac45a276aee18ba8e2a97b741818059ecb7dbceacf664a4bc8512e7b16938485ab9f7af85e90fb81abf743c3e3bb4370ac6799d99257819dde80760ef81f12b7740e2968cf26863340c2f9c0662222e2404c02726e6176de274cb60eda7d0bc3085a06afc50122fc3798268c6d15c5f3a8ef9857a607c234169e23a8c2883d18a931b4f2407ac1f3a1f12546f0bd824b59959efbb32fc6764a8c8869721566bec91249c677d704027c94348fd9c8f38ba981ccfcf319933d0da105ba9af80cc4ebbb62c628be0a7283364a543e2c6094cc5ecd06ac231b50b60e6d31c68413c5c2f1069cfeed076d0b0dfd76177ad8a057a10a6f84956bd87c57e46d64a75106b2dc2965264402da33281bad691ab86dd35f8e78806100d0b79707c910adf4223e7b0b886a0b0e83d350f62d2eab1ee8ce8c56ba6ab86eb5e341a1d77c2180c6fd2cd5a887a5071779f04ab4201aa8b378f17e449e7bd6a43d9cadbcc8f956cdc15955b115b908aa0667b1e02827f2bce65e29aa933ec07cf111043f7187bd92b29b7a2597c80eace7e56a49c61ff394df56483e6481bd3dbe410d16589c2059a6abcd8b49af06447ad1d600b1e06abb20062a72f6d4f260cb98fdb22c477488f0f92b046ea50172eaa25f2a2a57d49275ba0464054cd61965285e6b625b51df05d76cc375200859881d2027945595fcaccbaaf1d635455315913e9a9857051bf81e7092febc0d775800f74c05f606371c104921867bc4ed094459491a533b7dbf792354a16a0c12a91711c4708e55270af81a5e27edbe0999088475049195a60f4c170093a701'
        tsx_bin = base64.b16decode(tsx_hex, True)
        reader = x.MemoryReaderWriter(bytearray(tsx_bin))
        ar = x.Archive(reader, False, xmr.hf_versions(9))

        msg = xmr.Transaction()
        await ar.message(msg)
        self.assertIsNotNone(msg)
        self.assertEqual(len(reader.get_buffer()), 0)  # no data left to read
        self.assertEqual(len(msg.extra), 44)
        self.assertEqual(msg.extra[0], 2)
        self.assertEqual(msg.extra[43], 199)
        self.assertEqual(msg.version, 2)
        self.assertEqual(msg.unlock_time, 0)
        self.assertEqual(len(msg.vin), 2)
        self.assertEqual(len(msg.vout), 2)
        self.assertEqual(msg.vin[0].amount, 90000000000)
        self.assertEqual(msg.vin[1].amount, 7000000000000)
        self.assertEqual(msg.vin[0].key_offsets, [0, 45, 68])
        self.assertEqual(msg.vin[1].key_offsets, [5, 79, 38])
        self.assertEqual(len(msg.vin[0].k_image), 32)
        self.assertEqual(msg.vout[0].amount, 0)
        self.assertEqual(msg.vout[1].amount, 0)
        self.assertIsNotNone(msg.rct_signatures)

        self.assertEqual(msg.rct_signatures.type, 2)
        self.assertEqual(msg.rct_signatures.txnFee, 26000000000)
        self.assertEqual(len(msg.rct_signatures.pseudoOuts), 2)
        self.assertEqual(msg.rct_signatures.pseudoOuts[0][0], 161)
        self.assertEqual(msg.rct_signatures.pseudoOuts[1][0], 229)
        self.assertEqual(len(msg.rct_signatures.outPk), 2)
        self.assertEqual(msg.rct_signatures.outPk[0].mask[0], 0x8f)
        self.assertEqual(msg.rct_signatures.outPk[1].mask[0], 0xfd)
        self.assertEqual(len(msg.rct_signatures.ecdhInfo), 2)
        self.assertEqual(msg.rct_signatures.ecdhInfo[0].mask[0], 0xf6)
        self.assertEqual(msg.rct_signatures.ecdhInfo[1].mask[0], 0x85)

        self.assertEqual(msg.rct_signatures.p.MGs[0].cc[0], 0x17)
        self.assertEqual(len(msg.rct_signatures.p.MGs[0].ss), 3)
        self.assertEqual(len(msg.rct_signatures.p.MGs[0].ss[0]), 2)
        self.assertEqual(msg.rct_signatures.p.MGs[0].ss[0][0][0], 243)
        self.assertEqual(msg.rct_signatures.p.MGs[0].ss[0][1][0], 2)
        self.assertEqual(msg.rct_signatures.p.MGs[0].ss[1][0][0], 114)
        self.assertEqual(msg.rct_signatures.p.MGs[0].ss[1][1][0], 109)
        self.assertEqual(msg.rct_signatures.p.MGs[0].ss[2][0][0], 218)
        self.assertEqual(msg.rct_signatures.p.MGs[0].ss[2][1][0], 131)
        self.assertEqual(msg.rct_signatures.p.MGs[1].cc[0], 0x12)
        self.assertEqual(msg.rct_signatures.p.rangeSigs[1].Ci[0][0], 0xeb)
        self.assertEqual(msg.rct_signatures.p.rangeSigs[1].Ci[63][0], 0xfc)
        self.assertEqual(msg.rct_signatures.p.rangeSigs[1].asig.ee[0], 0xe7)

    async def test_tx_unsigned(self):
        """
        Unsigned transaction, forzen at certain version
        :return:
        """
        unsigned_tx = pkg_resources.resource_string(__name__, os.path.join('data', 'tx_unsigned_01_bc.txt'))

        reader = x.MemoryReaderWriter(bytearray(unsigned_tx))
        ar = x.Archive(reader, False, xmr.hf_versions(9))

        msg = xmr.UnsignedTxSet()
        await ar.root()
        await ar.message(msg)
        self.assertEqual(len(msg.txes), 1)
        self.assertEqual(len(msg.transfers), 36)
        self.assertEqual(msg.transfers[35].m_block_height, 6)
        self.assertEqual(msg.transfers[35].m_global_output_index, 5)

        writer = x.MemoryReaderWriter()
        ar2 = x.Archive(writer, True, xmr.hf_versions(9))
        await ar2.root()
        await ar2.message(msg)
        self.assertEqual(unsigned_tx, bytearray(writer.get_buffer()))

        ar2 = x.Archive(writer, True, xmr.hf_versions(9))
        await ar2.root()
        await ar2.message(msg)

    async def test_versions(self):
        dest = xmr.TxDestinationEntry()
        dest.original = "test"
        dest.amount = 1234
        dest.addr = xmr.AccountPublicAddress(m_spend_public_key=bytearray(32), m_view_public_key=bytearray(32))
        dest.is_integrated = True
        dest.is_subaddress = True

        writer = x.MemoryReaderWriter()
        ar2 = x.Archive(writer, True, xmr.hf_versions(10))
        await ar2.root()
        await ar2.message(dest)

        reader = x.MemoryReaderWriter(writer.get_buffer())
        ar = x.Archive(reader, False, xmr.hf_versions(10))
        msg = xmr.TxDestinationEntry()
        await ar.root()
        await ar.message(msg)
        self.assertTrue(reader.is_empty())
        self.assertEqual(msg, dest)

        # Reading as v9 causes problems as CN does not have versioning in the format
        # thus parser cannot determine on its own
        msg = xmr.TxDestinationEntry()
        with self.assertRaises(Exception):
            reader = x.MemoryReaderWriter(writer.get_buffer())
            ar = x.Archive(reader, False, xmr.hf_versions(9))
            await ar.root()
            await ar.message(msg)
            if not reader.is_empty():
                raise ValueError('Buffer not read completelly')  # expected in this case
        self.assertNotEqual(msg, dest)

        # Serialize as v9
        writer2 = x.MemoryReaderWriter()
        ar2 = x.Archive(writer2, True, xmr.hf_versions(9))
        del (dest.original, dest.is_integrated)
        await ar2.root()
        await ar2.message(dest)

        reader = x.MemoryReaderWriter(writer2.get_buffer())
        ar = x.Archive(reader, False, xmr.hf_versions(9))
        msg = xmr.TxDestinationEntry()
        await ar.root()
        await ar.message(msg)
        self.assertTrue(reader.is_empty())
        self.assertEqual(msg, dest)
        self.assertNotEqual(len(writer.get_buffer()), len(writer2.get_buffer()))

    async def test_transaction_hp13(self):
        tsx_hex = b'02000402000b4907011714b2010f01137e5ece45009ab1e29ae1bbd59e62935d20cf3689d8f0ca76396b354a56c345d7fb7902000b0750110d3c135da3011e430fbc864007b79d7df806a2daa2cf0adadaa1bd58b492fdcabfae4050d5799a1e4602000b4a0c022d05870119295d2354859858950a696ecf392e20240ada53be67c087992b5a033b01665d871198f3f502000b0420200f3a62217315ac010a7fd19e76fd7f0398795a40617a51c920106670652a52788252885c79a25a002a03000266a1029a838ec7c91656d3a7255d3d23cb5a1990b3bd0824ccabe8cee28ee58f0002fca72a9cfcbc75dcd4cfedf5ffde3dfd4da62449344ed6c9a6c9c1bfae5882c400029572a30b184838d0ca3c9e837fbf8e3e871e5c76bbbfdb7bdadd2575c96882a083010175018c3247f839e3b658da006d914b7cdb03a30001e227d65c2047f5e44356e40403b7840b5ab4fdaeee31082488a3d0fc2b397186ca8c37690ca6c6f969d02f0e5ef0804914e7ad6117d70962981eb455f983d1aaa9e8e7cfd70e8831e0ce9a63cf9ba08d8a84a12cbab1d1a0aa915c78eb1517cea6c16c3e0c1bfced7dc621a44d058088aca3cf0284c03d449864b2b47c0c221d2838a7f6bdc17139b12424827aed2303152ae5541e9685b90a07be65e1718c0fe9fa8223d3f13aed15b90b80b550004c54f51d9b53f2e078fd3f4359de14d094e8d2b5dcb4f38da178b2be1dec458f6233ce4c52bbd4479f37459e92d3009fc041130a790d236426533059a90127c4fd1b5ef998e2b59f249fb9d11f3ebc694c10d49faa8abfde62d8e20cd40bf2200d7cdcb8fb7d891fef3c3a6bf3afcddcbcb4eab1691f81d3466f006af86da80df3dc6e44b24fb92dc808fc585459f9134201b98f4da853832943fb49947a93230f19813f4a08dbfb622f6aa833242e1e3665604e3f74b9fc54f64f3cca5545c75cafd802795f3088be5df2d111c54d64f78d9e1ee53d0a9c48845226430fb71bf568b8eef605617c43a2de46eb9607451034d261e74bf20dc35a19c94c0f0858a5736936530fa448d5e36067bc48fc0264a904594e689712ca67ba8c270726d1e41e1fc599f144cdecff5920c98ff4dec717f64e47fb57543c6199c679d33654ed7b291c37b32c6da208ed3d9521b8ecf80aaffb4ad19a05834c7c0c7203e298b844505a4a523a3c6a142b293a5d0521b361d7639b5d30fe06d294a29682ddc18a0a467b6f41c9865984e470dfac9ea583f0d86dcae828d737b75802e8fde2c214e1f79d3f0fc70928492c96019ad0b31e088e3b567253af9b34a88e4979b0e77e4092b2ad8c2b83a2523d81c7eebb9d5bc48c20be89c399b9f46f3822244bbd1d63ecece2a353d056ab3ed7424ac50e7dbbb2019f6b1065e1e9b03abf5b6d08ad757a96f1c960b66308cde063845947101593914f8cdbec78daa8a86dccdb06a5e46819dafffcce813a2e4a04c604957937a91f073813d5ccd410fe6cecb3ff927dc74d0c19a51a65c79efb72023298947edc44579a6169e193d881001b021e9b842800a4fc0ed71f5f1527cd4de03d95a9a319526022032ff1aad4aceb9875f2152f6ebc4c40c598d24c5165e13aeeda0a8c38c459f4f97857f7042c67caf54695c58839ea1989031b5a5391c427debbc0f0a2a401373c44ef931d062cd0896d2eb23b1400e6344d5f4fe477eb3def50a3be8afd28b8e6173aa61b8886c5e20aeb3ec6b1ff7909e8d9f9c87267321109265abb48e3ed28b5bfb1149141501ecf22a8d77595498714b79bfb34246a0418c7c4c1ab8732623afbc32ab478180680361d243aae7eb2c100ec88f0603cf449297127e887f664144c3c3e47465f0060cdd1d74fa6d470a96ce29e3b6480b3a33026a37ef38d1fa6f933c57b08e40cf22f2852fcd9294c276a3b777b9dc203a8c34261e7d22fe21ab3735fb167350c6fe9c805f1d57a65189e701097cb938c50985c726f8fa2cf0276ad8e79bd740ee3357b94ed0106acde8236f5d0e0e30cdf39abd653bfaf0618f94b1abf940f078c5a4a26f0c3ebcd93f4237cf82a16196812def6a752330ddaaf476d71bd6d05b4f8d654f8bbfba3fbbc8ef03fc8832010bf21602f07d638c20ac11939cb7702a3d7409f4fde8950e668e12a24fcc94fb800c3e7b74c97c5aac28d0b0192cb007fef1458c1845175a85e4e7ae6f29f15607774163f434970927719b2c931a00a19c54fbc2a8d6cf7098187b7f60f8a5308c33c2bc70a02b07ac9430a91ca1001e25a3cb9b638c59aa14de6e497f20f8ab083f6e54fc39bfe6258e04c597c9c08c8ca176fb796e964aa76823a2e5a6dcc5759d0a1d78c34314ac4366d2167a605918a791a4364f1ac41fd51deceaec81a00e4ccbf5f87aee032ad8267e9aaf508758963c0e8efad5fcd3a5a416b40efcc139266569fd783346c7e7ad8b189e908e6b4068a2609786c32cbc59c61a0e2ae7919839d7b943912faac2db8b31bf7f5aed509cecdf4089ac88897929de7e66c30b68634cf538d5ee2ae3788d9e0020b09e589412f5f1e93993e023cb7523e9e01eeec27bc5ce76cbbe5c4231117620a59e215366b8963f149d0d37337963d08481418fc07abc49cba6c3f42d194230d81fc38c272cd7f99b17426e57e5f19c5effc7bcd8f6bf2c5a2639061998e4803e2df454b2c6935f596cf8ea32a64596697fa44dd173da06d8a37289d61c1140a1d507208196cf03f2891741294a57da53fad15359f3fd07c7288e2c2294d6f077434d56e43d57cefc67949f66d0605e9e8b4e4b22793c81c5af60efcf151230e47afc4c25d6126c9a58e93cfe16afd0390b17c93af5793bf4221f13bb9ef5f0ace3e71a0e27a42e9dd233754d05fdf573743fc4c37ad7e382aa9407e8146380e09839331d041f19d6fd995683a056003df0956b9bfb39ce4122ea9d54976230e8613bba4c528c52960fc12ef5556129987a5d090478b43e3fa4f4a4a119f7c0d75da91c608d8e14b515605b4f0122cd4156b81b5f98a66cdf24d631ded93b60985559f234be3457c270d24983cb1394938c82b68de3ecbd030d04fff7419c434401fff455a411292eda440ab722b09786857e070a7d3cee3da3c93e171e6710c51e30a6c68a819e144a0d517adea4045a1c8fadaa5452edb2511f93b3681ff0e374d8f028e06ce2d151298d991b7862880b633a0df3746ccb2a3090b692f870f4c92c2ecb018fd3954c28927b81dfc7427e603f567933db59a79595e317c770d0220d96d56fb657dc1ef3b7638ee21dfcf0ac2f4ef5fe808820ccca4f9617900fb5f77183d4a30abf3bfb456efcf7f9777c42c1a77bdb4966afcb867c100c00b10f4ce9c5f5fb1b9329702bb15312d8d1fb3d6d7ffcbd43b52e96bfb8978e208a0587ffd396bd1944d05851053504844c876a69287abbe9b3a73a4dd51e95b04dbee2b4c275c3208dfdcabeabbaf7e0a70af56ec0f7cace8223a16e419730b0a75a6c09d91dee97940317395cc568d6217fdf55d975d1cbc0adee83ae135b401cc550653bb96dc5ade1cf475a5de024fc0ff66221f7050fff2fe3733a9517d0bedf8c06ecb55d7bd40ce2f122dbab4b90ea2aca886ffbfc8ba0c8d6906c4c5057acb26b88e0eab23cc0912afa07f6b63a125f26ac9297268e09194f2297935469556aef9bb2052e46b411445d91059b5507dbc7c6f30bfe802a347f679063704f685dc43759800bf50c8c7198651f2b7f786f5e7f79de505ea6227734135b20fc922a5aa8fde3c632f4fa1dcf97f9ff89ec537757fbca1b5d21f274f093d9b03709b68c003e19a050abffac660deecb193aa94bb3666195c1842942e5cf43a0f44b01c03d3fec20916f6784f7d36c67fb8856a05b70d1703aa8ff0ea01fb7d0bcbf422b657498b6a4e0861816c84f01e609c0c163f24c1a692e4d532c9ba9f0ce035c15e7a27915e8d148316939682490888d9eac70b761e7ad68df791730104a0a83032afeaa8df418ae6e4e5e8283dafe82b064fe48fc462056cd85945a20a1d731ddda4c39c7f33f76ecd01fce986585eb2d5d7cdac5e4a1138ff215065091f57c4fae08723ba474757f40683638c0089ef1c5fe82e86329aad6ee9b39105f2a4aa52fcca67ba26a766477bb642c5a708baafe753bc201a40fc20b190520d150f2904130a213cd32641e09f21bca9773e2403acd093f6d60ec5d6fd1a9c01fbd1ce6e9139292ca1c1835f13d523d845b1a0d934199876fbc5f5229b0fddd2629d43412f3ae64774571d01acaba20205aee4e32bbd0bb84421de7a6f32e6275735f77d021afcde6884c64fad9d0c164327a56a7d769a99472ba45e475574e56f46936357a770f0176f2a2ad8baae7921c8c74f6894d251acda5ae2624e1f8f8158163867802871815afff978e4ac6106cc1a002a76525eed815869de6a6e86'
        tsx_hash = b'feef88257730d444bff75ffa9f4c985d06810b544b247cfe8105070a0f897dc9'
        tsx_bin = base64.b16decode(tsx_hex, True)
        reader = x.MemoryReaderWriter(bytearray(tsx_bin))
        ar = x.Archive(reader, False, xmr.hf_versions(13))

        msg = xmr.Transaction()
        await ar.message(msg)
        self.assertIsNotNone(msg)
        self.assertEqual(len(reader.get_buffer()), 0)  # no data left to read
        self.assertEqual(bytes(msg.extra), binascii.unhexlify(b'0175018c3247f839e3b658da006d914b7cdb03a30001e227d65c2047f5e44356e40403b7840b5ab4fdaeee31082488a3d0fc2b397186ca8c37690ca6c6f969d02f0e5ef0804914e7ad6117d70962981eb455f983d1aaa9e8e7cfd70e8831e0ce9a63cf9ba08d8a84a12cbab1d1a0aa915c78eb1517cea6c16c3e0c1bfced7dc621a44d'))
        self.assertEqual(len(msg.vin), 4)
        self.assertEqual(len(msg.vout), 3)
        self.assertEqual(len(msg.rct_signatures.ecdhInfo), 3)
        self.assertEqual(msg.vin[-1].k_image, binascii.unhexlify(b'7fd19e76fd7f0398795a40617a51c920106670652a52788252885c79a25a002a'))
        self.assertEqual(msg.vout[-1].target.key, binascii.unhexlify(b'9572a30b184838d0ca3c9e837fbf8e3e871e5c76bbbfdb7bdadd2575c96882a0'))
        self.assertEqual(msg.rct_signatures.ecdhInfo[-1].amount[:8], binascii.unhexlify(b'bdc17139b1242482'))
        self.assertEqual(msg.rct_signatures.outPk[-1].mask, binascii.unhexlify(b'ec458f6233ce4c52bbd4479f37459e92d3009fc041130a790d236426533059a9'))
        self.assertEqual(len(msg.rct_signatures.p.bulletproofs), 1)
        self.assertEqual(msg.rct_signatures.p.bulletproofs[0].A, binascii.unhexlify(b'27c4fd1b5ef998e2b59f249fb9d11f3ebc694c10d49faa8abfde62d8e20cd40b'))
        self.assertEqual(msg.rct_signatures.p.bulletproofs[0].L[-1], binascii.unhexlify(b'bd1d63ecece2a353d056ab3ed7424ac50e7dbbb2019f6b1065e1e9b03abf5b6d'))
        self.assertEqual(msg.rct_signatures.p.bulletproofs[0].R[-1], binascii.unhexlify(b'0aeb3ec6b1ff7909e8d9f9c87267321109265abb48e3ed28b5bfb1149141501e'))
        self.assertEqual(msg.rct_signatures.p.bulletproofs[0].t, binascii.unhexlify(b'60cdd1d74fa6d470a96ce29e3b6480b3a33026a37ef38d1fa6f933c57b08e40c'))
        self.assertEqual(len(msg.rct_signatures.p.CLSAGs), 4)
        self.assertEqual(bytes(msg.rct_signatures.p.CLSAGs[-1].s[-1]), binascii.unhexlify(b'f2a4aa52fcca67ba26a766477bb642c5a708baafe753bc201a40fc20b190520d'))
        self.assertEqual(msg.rct_signatures.p.CLSAGs[-1].D, binascii.unhexlify(b'fbd1ce6e9139292ca1c1835f13d523d845b1a0d934199876fbc5f5229b0fddd2'))
        self.assertEqual(len(msg.rct_signatures.p.pseudoOuts), 4)
        self.assertEqual(bytes(msg.rct_signatures.p.pseudoOuts[-1]), binascii.unhexlify(b'8158163867802871815afff978e4ac6106cc1a002a76525eed815869de6a6e86'))

    async def test_transaction_hp15(self):
        tsx_hex = b'02000402001012453b5503b60132181e0d310701050e9a01bc864007b79d7df806a2daa2cf0adadaa1bd58b492fdcabfae4050d5799a1e4602001006460a364b441d30149e01194711670726859858950a696ecf392e20240ada53be67c087992b5a033b01665d871198f3f50200105303321704691d3008571f0b1e565b217fd19e76fd7f0398795a40617a51c920106670652a52788252885c79a25a002a020010344f0605061e5607642f1e073470511b3fb14be28cca0ee8b58a4f076c09aa102b07e338233b16b53cb7ad38ffb5d45e030002d66623c9a469d26d414f74727400eaa814d41f14bc0643a171b3ebfd4009c5760002d4856dbaeb4a0fab9727b0cd2508f713a6abc398c3e04aa4ba2cf8ea08004efa0002f56bbbf350081b91df2bb172ab6e59d796e7fe1dbf6b843d9c31e0313ab00f5c83010179d2220681956bf57ba65e0aed058e7a98e0eea2a9cbe068aaf2b4708a4fdddb040308927450d502c04d66aba11372995a39e277518b9a9c95713e1320ac81ec41de6561c4f77b5252465c527fecbe57aa4e7648f5b1738698a10a27b3a7a9e722c31becf3d80d66d47d3c098b1dc1d4104b53b340e14deb5e42310f66c36a687a49068088aca3cf02ef7b3e9a15ccf946b9818facc57b6d617be3b0cc9e231d9bd032a83f6bb4944d5418ac850ff5b8911a802b13b0aeda84ea43f35037bb4ff69d138a7222c5fb478f81ad6c6eaf68ce84071af478bfc46779cf6b1cf999de21b3bde4fa270b0ecda666c0c0f11bc428b95d74d4a935a154f27dbd6d2b3ecc76019b32c234ca27203c296f7a42b5fb35e37bdf238d5f33e4394cc076aca529c88d8ac4c8859214678df3621283879f5084fc4fbd048c7e6d843112d2cb790cab81dd48d3e627096bcd5f7e77ac70f7e32fc0e8ed4a30d453d855e7fc3cda72f1764742132a2e2f19f6dc0d6c17f4901d3e1b627d441ddc984d9aed42f22b64210b6c5dccdb719e84564533ad0c6100bb50f7cad5842872d623e07dc3e6a7d2f105a1f957ad042641e880800026d5019fe9451cd0526c0cca20e786cfb6661ac00908a9b2d9041f090996bfe9b8fc39c065340c35233bcd9205bf36931575e8f0538b705854c22266a5b735eca0cb8fb2eefd21bff086acf0c8cae454c2c184933849bb5118fff439af19f444331d3ac63f8a0bd7526d4863b1364e49cba015dc27a3e7b3926409d37bfac838e718202c53f63358da2e2d7b6e86a0adb37c4149adb338fb5748325146b239e9c7743ae0cb1a3bfb109a049eb23058a055b91afbeac92139892524900c88f2b73acedf1863b907fa83601c6db8f3fe6e097b5b0cb0c62fdb541e87809a7b1c285c9e75ae089f7f836de2dc8b8242fd8d7c70af78fd629c6096bb783d466ef43ef6893bd0838ca114474c4ebc5f1c200b32966916d90808f3917cdaee405adcbf20b0471fb16b2bcd18531ea33d67a87e2fd83b45566ac3520e0c508ef34dc40f2d457dec1f57bd1a9566bdcc6b3cbf38f309af1ddd5f0325ccada6c07463d0a6b58bdad03f55bb13e4bb3fa375a2f4ad7820ba5059689a1002bc3c894a8c52bd5853bb13faa8c63066f7886e1c37ec338ab88a658251bc5c980727f2e49382d6a1b8fbe9129a4306a69f7e464136bddeff959c5b29274080a7b6bd1cf9dd5c22c0e1189b6aa22344ad6bd7e03e16683c65eba49da589af8d9c66cbbc111a266f76e983ba32770706a376d34b02f4dbabb2419863d771de3483c825715840b81decbbadd0613f5bd3a6ae95363f6b66d3816c137ab81f66a17cdbe5877ee3d2c73e0c8bb13a5cd5f6902a19f71f93a1eafcc22e4107f50fbfc4d896667f4db04864bf91266ddd311f182b04ece4bed05b886085196e8d0d71278145180bac5e17c24c46c2c5c4dec60072cf87ad10453a8d9a55513b370486a5565a3a02cec85513d27de858df926f79939c0fbe3ece2294cf4419055107a42b05c3b382197676e848295dc547151807cc2f97dff6a50a78cddce107ac09b010c2ae7e93114cd2fcc995351a6b08bf49fe881f327bb6f2d8af7ba9636f04d869c7f7860ac5d73a381ccf7d8e6b8267e16044a7d55152da5606e37138a605c763c1bedd8b66e525b744f661799f850f6efe242feac43cc29154a639a6bf0c4e8384b462f5074c5d5c8dfd503e43d0b78f35efb78f62c2aa29926901cd0e076cc2f6e2dbdaf9107e52b505c557d0d360e638933fe67ce192beaaefc9cc4a0c2cd0c5c1107dae60331bea9918e1295508128fa7c70daa827af0fdf891c50e0bb3fe93c194a9d9286ca7e3830761d32dafb292334f2644c1625fdff159d75905b53dede6d10cb1ba800a3ec00cdfa9985768f2c9d74fe9434aab167121220f0d91094da842d7488c42d49448cf99d72000d330f35faafba432745f86e9c5750034d60533038c2712864185962dab645fa89224e8e75521eb1a5ae9d8b1e2b8060789c91c1ef0e78d654e08dda1a711f14f47789c6f72c41102fdd7957998670c2bcc486106907f18c0582a3ec4eee55fb50d95057934ef46739080350e147106b056f58d96046f50aa37ec3ed43fb3e873b838356ca9f0e487845ea285b710699ca23995c0cc58d0234780e947bcbb7f7753fc557700394a6a6322c3c13b240e8bbe20e9170891d30e386cc12c71487e20229814ff6ee13a523002e38913ce0ac2d8566158dc3a18c9ef0da68dabb77ea1acbe16f8eff21cca40cfa56a2af9066e8f65ad8de373a18828e6de5d844b3af02bd7078fce4da8a26aa6f499e9300124c6ee78335b05ddf6e60580ddb1c7a49809068a170068968a1eff51617c080856537316cab5d3bca591b7b0f8a2aaee3e9cf8809f629019724f96b12968da061f2063e2552c408a3dadf9b699883571e783256227168d0c5a9d3b40f1ccf10db9f67f2ac0413bc49f78c1d4a93ab46e8f60d7f1af3ae8c242a8b264b9cafd06d720335539161b29c09138201f1b38d038d2ac1d37f06f212a1033fe81819101ff180f6341a00ebe27c45d34671a5994e0781827bf56b6c61275e8724911a40fe5ce37e8418c03af30232579fc3f6c7987f4e01d478e9143fa76728e119a1002e718aeab7e7eb6ed44c99fee0125983030e5a0aacfb69b63e2b56430d93b16059df7b76b247ec03eb36f0ef5811a86d8d7ea462957f0b285cad1c6caa116d80c70509f463f5074639212c28bf5b46e7e7fa59513df5a7904b26a94b0694add012699cf56e5b1ad6e00b3a479755cdc8627b5a3bb6716d5ae9a203d3431f7900dd34396fa34eca1b58bc93af6a6dcf808cfb95b56ef42705082932496f93cc20623822b281a23e5770a66313361a58e32dd295a203db5c3549211b13a383c3004d13faebc04c59e65fc4cf5947b8dea1a41b20b78bba65b6750077620de9e7de192af50a5a6182cbc61140b493d3ec11328e317c2e3ce420a6301b07bc28c280b4db63d5889bcab52d846f48284ff8dfc6fde2fed0fdf6d1322415ac819ce490baec94b3242c890f4bd5165a830f45e7f170cf5a097200a3a0ac5ad66e1f0bd0dc3118bca64018eebfbfc58d55619f06bbfee47cc1f93f695f2c59976a96cbe0b9f5a429cd62465a2bd4b5df01995eb866726df3da756390adae32d107161d607daa4933fc439db954ef7ee3b83b806540f53453b2f8b9cfac2be6ded39eff4056a27d5e39ecb4d9f693306e3bf4dc497b814595bb7502e64aaf6d0a80136ed0717a473c8edafe3b0f5eb8dadf107b227600bcdb03fc7c005922bc3cbc955f609a790ca37c9a3a8ec0f22e0472f4f0aaf08d7a744c70e6a987afd23ad916e2b0f1b330d1b685314f51eebe81ffce88576b017c4e04f470418620cc71f59a00b0eeef62838829413ccfd30aba970ca1e34576d502ad790ad1b4af8f3f0210bfa0c585af28792d14f9ac5474fb36a80c19c00784f0c5f0b483e3261e636e9cebd0eb97f8b864ac77042aa3407e316ef37f5a7d71772e7d6f9961ae74d6fb10b020f5c117ba40b7d9551eeaeeb2675a95733502cd4516f13ad41022ace6d79e1d50e7bd97681bc7512a873f5058b6f8770d4f7150307f7e08ff7eac97e1a41702c01bfb8cd29013d2363e8399e1b27954981a034f7fc7f5f94b7d2666b0009d85c07c31b40f5d803cf512b10cc6894ff8299e3d6727c735429b1f081964cd3518f095e91a71716212d6bfb19015cc21a67effb995620847bbc7017a6510e0b61efd570ab99e5c97f76f19c70288d62a32630980e993e1741ddd28a6bd9746165cc0cd1f3f4ee823c65ea81789d430f71f95b4041ec749fc3adad723cba6429711b05581965cf06f433c2ba1347b5fdb38db5e7c88d212797560d5a2add2cf1f55305b90bd247c052c4029f557d47aa734cb18f45488bafdbe1e542d5855ab913a50b958e2db831680ee160eec3d16cb1211638573a7237b19dcc2add6bc381ea210c38f258c0f1c7e82ca50a9e26cba546e1df9d563abf379c2012e23a94499a410d1e48ec47f2d30759ad09495560eba8f886b9e365478f3343fa83122f11435f04d481f86e987272b81bc3f91ce0d7839f2f4afc5fcfd77de0e26206dad9043a02c384b39fef6877ef0633cd6bc4ff6b4bd8ef0e975731d947ca1e9e3da1ff740f967d81940a5ba1e8e57540fd38bacfa67f4a5ee7dfbb67d4b25755b36953170900b6430f1a695ed7ac29b5693369988728fa805567978f659aad1b6431200c0d87a804db9d89f5d8e519621522fd3574cf9ee118efe37ae782c0d436f985a20663d394e80f27dc15a79acb13e402414f78d83ef677c197eb6a30d88ec1a40d0b49cc36f00f7aab82af34b4b6792786fc1e472beaff4f1851529d71da899ce4055bf339368847cc67412d628114809d0de062823283dad209748538be1ad98a0e48cce058c23a415835bf2ace1a316d15f0909dd68fef9e11a217ebd999b29b074e45f48ba9cd75566bb627f5bf581df63a57a19cacb04fc68ea4227f7c79670722ecf95a1d34b93caf840fb39c9dac67f0ba2cf47006fc4fdcc81e45d0f99562f8f84210a844c1c39bdd0c0f6007f80855b44679041de38f1744e98c33b0cd4455aa7ba66c5eb159dd63edeea12183101a703aeb20340e43248f00bcc1eba270885186f4d02bb2250b6bf459311fe1f00139c3b342ceac7bedc23508e9c6fd9c6e2dde4e065d98c807053fc75c8a6ebc684dc46f534d035cd7e8b28d6547a7ce'
        tsx_hash = b'5ca2e704d65055860fc96c94858cffdcccae744c533407d7ccaa6c03dbea95fd'
        tsx_bin = base64.b16decode(tsx_hex, True)
        reader = x.MemoryReaderWriter(bytearray(tsx_bin))
        ar = x.Archive(reader, False, xmr.hf_versions(15))

        msg = xmr.Transaction()
        await ar.message(msg)
        self.assertIsNotNone(msg)
        self.assertEqual(len(reader.get_buffer()), 0)  # no data left to read
        self.assertEqual(bytes(msg.extra), binascii.unhexlify(b'0179d2220681956bf57ba65e0aed058e7a98e0eea2a9cbe068aaf2b4708a4fdddb040308927450d502c04d66aba11372995a39e277518b9a9c95713e1320ac81ec41de6561c4f77b5252465c527fecbe57aa4e7648f5b1738698a10a27b3a7a9e722c31becf3d80d66d47d3c098b1dc1d4104b53b340e14deb5e42310f66c36a687a49'))
        self.assertEqual(len(msg.vin), 4)
        self.assertEqual(len(msg.vout), 3)
        self.assertEqual(len(msg.rct_signatures.ecdhInfo), 3)
        self.assertEqual(msg.vin[-1].k_image, binascii.unhexlify(b'3fb14be28cca0ee8b58a4f076c09aa102b07e338233b16b53cb7ad38ffb5d45e'))
        self.assertEqual(msg.vout[-1].target.key, binascii.unhexlify(b'f56bbbf350081b91df2bb172ab6e59d796e7fe1dbf6b843d9c31e0313ab00f5c'))
        self.assertEqual(msg.rct_signatures.ecdhInfo[-1].amount[:8], binascii.unhexlify(b'7be3b0cc9e231d9b'))
        self.assertEqual(msg.rct_signatures.outPk[-1].mask, binascii.unhexlify(b'b3bde4fa270b0ecda666c0c0f11bc428b95d74d4a935a154f27dbd6d2b3ecc76'))
        self.assertEqual(len(msg.rct_signatures.p.bulletproofs_plus), 1)
        self.assertEqual(msg.rct_signatures.p.bulletproofs_plus[0].A, binascii.unhexlify(b'9b32c234ca27203c296f7a42b5fb35e37bdf238d5f33e4394cc076aca529c88d'))
        self.assertEqual(msg.rct_signatures.p.bulletproofs_plus[0].d1, binascii.unhexlify(b'a1f957ad042641e880800026d5019fe9451cd0526c0cca20e786cfb6661ac009'))
        self.assertEqual(msg.rct_signatures.p.bulletproofs_plus[0].L[-1], binascii.unhexlify(b'9c6096bb783d466ef43ef6893bd0838ca114474c4ebc5f1c200b32966916d908'))
        self.assertEqual(msg.rct_signatures.p.bulletproofs_plus[0].R[-1], binascii.unhexlify(b'3483c825715840b81decbbadd0613f5bd3a6ae95363f6b66d3816c137ab81f66'))
        self.assertEqual(len(msg.rct_signatures.p.CLSAGs), 4)
        self.assertEqual(bytes(msg.rct_signatures.p.CLSAGs[-1].s[-1]), binascii.unhexlify(b'48cce058c23a415835bf2ace1a316d15f0909dd68fef9e11a217ebd999b29b07'))
        self.assertEqual(msg.rct_signatures.p.CLSAGs[-1].D, binascii.unhexlify(b'22ecf95a1d34b93caf840fb39c9dac67f0ba2cf47006fc4fdcc81e45d0f99562'))
        self.assertEqual(len(msg.rct_signatures.p.pseudoOuts), 4)
        self.assertEqual(bytes(msg.rct_signatures.p.pseudoOuts[-1]), binascii.unhexlify(b'6e2dde4e065d98c807053fc75c8a6ebc684dc46f534d035cd7e8b28d6547a7ce'))


if __name__ == "__main__":
    unittest.main()  # pragma: no cover


