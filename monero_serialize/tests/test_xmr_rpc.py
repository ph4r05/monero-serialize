#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import binascii
import unittest
import json
import pkg_resources

import asyncio
import aiounittest

from .. import xmrserialize as x
from .. import xmrtypes as xmr
from .. import xmrobj as xmro
from .. import xmrjson as xmrjs
from .. import xmrrpc


__author__ = 'dusanklinec'


class XmrRpcTest(aiounittest.AsyncTestCase):
    """Simple tests"""

    def __init__(self, *args, **kwargs):
        super(XmrRpcTest, self).__init__(*args, **kwargs)

    async def test_simple_msg(self):
        """
        TxinGen
        :return:
        """
        data = b'01110101010102010108146d5f6372656174696f6e5f74696d657374616d70057099935300000000066d5f6b6579730c0c116d5f6163636f756e745f616464726573730c08126d5f7370656e645f7075626c69635f6b65790a805a10cca900ee47a7f412cd661b29f5ab356d6a1951884593bb170b5ec8b6f2e8116d5f766965775f7075626c69635f6b65790a803b1da411527d062c9fedeb2dad669f2f5585a00a88462b8c95c809a630e5734c126d5f7370656e645f7365637265745f6b65790a80f2644a3dd97d43e87887e74d1691d52baa0614206ad1b0c239ff4aa3b501750a116d5f766965775f7365637265745f6b65790a804ce88c168e0f5f8d6524f712d5f8d7d83233b1e7a2a60b5aba5206cc0ea2bc08'
        data_bin = binascii.unhexlify(data)

        reader = x.MemoryReaderWriter(bytearray(data_bin))
        ar = xmrrpc.Archive(reader, False, modeled=True)

        section = {}
        await ar.root()
        await ar.section(section)
        self.assertIn('m_creation_timestamp', section)
        self.assertIn('m_keys', section)
        self.assertIn('m_account_address', section['m_keys'])
        self.assertIn('m_spend_public_key', section['m_keys']['m_account_address'])

        writer = x.MemoryReaderWriter()
        arw = xmrrpc.Archive(writer, True)
        await arw.root()
        await arw.section(section)

        reader2 = x.MemoryReaderWriter(bytearray(data_bin))
        ar2 = xmrrpc.Archive(reader2, False, modeled=False)

        section2 = {}
        await ar2.root()
        await ar2.section(section2)

        self.assertEqual(section['m_creation_timestamp'], section2['m_creation_timestamp'])
        self.assertDictEqual(section, section2)

    async def test_modeler(self):
        msg = xmr.AccountPublicAddress()
        msg.m_spend_public_key = b'\xff'*32
        msg.m_view_public_key = b'\xee'*32
        mdl = xmrrpc.Modeler(True)

        m2 = xmr.AccountKeys()
        m2.m_account_address = msg
        m2.m_spend_secret_key = b'\x12'*32
        m2.m_view_secret_key = b'\x15'*32
        m2.m_multisig_keys = [b'\x19'*32, b'\x22'*32]

        obj = await mdl.message(msg=m2)
        self.assertIsNotNone(obj)

        m2.m_multisig_keys = None
        obj = await mdl.message(msg=m2)
        self.assertIsNotNone(obj)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover



