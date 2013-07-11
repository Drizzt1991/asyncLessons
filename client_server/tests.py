##### -*- coding:utf-8 -*- #######

from protocol import package_read, package_write, BrokenPackage
from unittest import TestCase


class TestProtocol(TestCase):

    packages = [
        # Simple package
        (b'Some data',
            b'\t\x00\x00\x00\x00\x005b82f8bf4df2bfb0e66ccaa7306fd024Some data'),
        # Null package
        (b'', b'\x00\x00\x00\x00\x00\x00d41d8cd98f00b204e9800998ecf8427e'),
        # UTF-8 package
        ((u'Стр').encode('utf-8'),
            b'\x06\x00\x00\x00\x00\x00001e1820392a1c4cd9fcc511bd673da5\xd0\xa1\xd1\x82\xd1\x80')
    ]

    def test_write(self):
        for raw, packaged in self.packages:
            self.assertEqual(package_write(raw), packaged)

    def test_read_simple(self):
        for raw, packaged in self.packages:
            self.assertEqual(package_read(packaged), ([raw], b''))

    def test_read_enhanced(self):
        # Read empty input
        self.assertEqual(package_read(b''), ([], b''))
        # Read 0 packages
        self.assertEqual(package_read(b'\t'), ([], b'\t'))
        # Read 2 packages with tail
        self.assertEqual(
            package_read(
                b'\t\x00\x00\x00\x00\x00'
                b'5b82f8bf4df2bfb0e66ccaa7306fd024Some data'
                b'\x00\x00\x00\x00\x00\x00d41d8cd98f00b204e9800998ecf8427e'
                b'\x08'),
            ([b'Some data', b''], b'\x08')
        )

    def test_read_broken(self):
        # Read broken header
        self.assertRaises(
            BrokenPackage,
            package_read,
            (b'\t\x00\x00\x00\x22\x00'
             b'5b82f8bf4df2bfb0e66ccaa7306fd024Some data')
        )
        # Read broken data
        self.assertRaises(
            BrokenPackage,
            package_read,
            (b'\t\x00\x00\x00\x00\x00'
             b'5b82f8bf4df2bfb0e66ccaa7306fd024Some dddd')
        )
