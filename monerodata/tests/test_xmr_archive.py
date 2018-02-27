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
        ar1 = x.Archive(writer, True)
        await ar1.message(msg)

        msg2 = xmr.TxinGen()
        ar2 = x.Archive(x.MemoryReaderWriter(writer.buffer), False)
        await ar2.message(msg2)

        self.assertEqual(msg.height, msg2.height)
        self.assertEqual(msg, msg2)

    async def test_boro_sig(self):
        """
        BoroSig
        :return:
        """
        msg = self.test_data.gen_borosig()

        writer = x.MemoryReaderWriter()
        ar1 = x.Archive(writer, True)
        await ar1.message(msg)

        msg2 = xmr.BoroSig()
        ar2 = x.Archive(x.MemoryReaderWriter(writer.buffer), False)
        await ar2.message(msg2)

        self.assertEqual(msg, msg2)




if __name__ == "__main__":
    unittest.main()  # pragma: no cover



