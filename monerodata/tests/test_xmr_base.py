#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import base64
import unittest
import pkg_resources

import asyncio
import aiounittest

from .. import xmrserialize as x
from .. import xmrtypes as xmr


__author__ = 'dusanklinec'


class XmrTypesBaseTest(aiounittest.AsyncTestCase):
    """Simple tests"""

    def __init__(self, *args, **kwargs):
        super(XmrTypesBaseTest, self).__init__(*args, **kwargs)

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
        pass



if __name__ == "__main__":
    unittest.main()  # pragma: no cover


