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


class XmrSerializeBaseTest(aiounittest.AsyncTestCase):
    """Simple tests"""

    def __init__(self, *args, **kwargs):
        super(XmrSerializeBaseTest, self).__init__(*args, **kwargs)

    async def test_varint(self):
        """
        Var int
        :return:
        """
        test_nums = [0, 1, 12, 44, 32, 63, 64, 127, 128, 255, 256, 1023, 1024, 8191, 8192,
                     2**16, 2**16 - 1, 2**32, 2**32 - 1, 2**64, 2**64 - 1, 2**72 - 1, 2**112]

        for test_num in test_nums:
            writer = x.MemoryReaderWriter()

            await x.dump_uvarint(writer, test_num)
            test_deser = await x.load_uvarint(x.MemoryReaderWriter(writer.buffer))

            self.assertEqual(test_num, test_deser)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover


