#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import base64
import unittest
import json
import pkg_resources

import asyncio
import aiounittest

from .test_data import XmrTestData
from .. import xmrserialize as x
from .. import xmrtypes as xmr
from .. import xmrobj as xmro
from .. import xmrjson as xmrjs


__author__ = 'dusanklinec'


class XmrJsonTest(aiounittest.AsyncTestCase):
    """Simple tests"""

    def __init__(self, *args, **kwargs):
        super(XmrJsonTest, self).__init__(*args, **kwargs)
        self.test_data = XmrTestData()

    def setUp(self):
            self.test_data.reset()

    async def test_simple_msg(self):
        """
        TxinGen
        :return:
        """
        msg = xmr.TxinGen(height=42)
        msg_dict = await xmro.dump_message(None, msg)
        js = xmrjs.json_dumps(msg_dict, indent=2)
        self.assertTrue(len(js) > 0)

        popo = json.loads(js)
        msg2 = await xmro.load_message(popo, msg.__class__)
        self.assertIsNotNone(msg2)
        self.assertEqual(msg, msg2)

    async def test_tx_prefix(self):
        """
        TransactionPrefix
        :return:
        """
        msg = self.test_data.gen_transaction_prefix()
        msg_dict = await xmro.dump_message(None, msg)
        js = xmrjs.json_dumps(msg_dict, indent=2)
        self.assertTrue(len(js) > 0)

        popo = json.loads(js)
        msg2 = await xmro.load_message(popo, msg.__class__)
        self.assertIsNotNone(msg2)
        self.assertEqual(msg, msg2)

    async def test_boro_sig(self):
        """
        BoroSig
        :return:
        """
        msg = self.test_data.gen_borosig()
        msg_dict = await xmro.dump_message(None, msg)
        js = xmrjs.json_dumps(msg_dict, indent=2)
        self.assertTrue(len(js) > 0)

        popo = json.loads(js)
        msg2 = await xmro.load_message(popo, msg.__class__)
        self.assertIsNotNone(msg2)
        self.assertEqual(msg, msg2)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover



