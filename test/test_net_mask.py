# Copyright (c) 2002-2011 IronPort Systems and Cisco Systems
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Unittests for ip module."""

__version__ = '$Revision: #4 $'

import unittest

from aplib.net.exceptions import MaskValidationError
from aplib.net.mask import Mask4, Mask6, MASK_FORMAT

class Test(unittest.TestCase):

    def test_mask(self):
        m = Mask4(0xffffff00)
        self.assertEqual(m.mask, 0xffffff00)
        self.assertEqual(m.prefixlen, 24)
        self.assertEqual(~m, Mask4(0xff))
        self.assertEqual(hex(m), '0xffffff00')
        self.assertEqual(m.format(), '0xffffff00')

        self.assertRaises(MaskValidationError, Mask4, -1)
        self.assertRaises(MaskValidationError, Mask4, 0xffffffff+1)

        m = Mask6(0xffffffffffffffff0000000000000000)
        self.assertEqual(m.mask, 0xffffffffffffffff0000000000000000)
        self.assertEqual(m.prefixlen, 64)
        self.assertEqual(~m, Mask6(0xffffffffffffffff))
        self.assertEqual(hex(m), '0xffffffffffffffff0000000000000000')
        self.assertEqual(m.format(), '0xffffffffffffffff0000000000000000')

        self.assertRaises(MaskValidationError, Mask6, -1)
        self.assertRaises(MaskValidationError, Mask6, 0xffffffffffffffffffffffffffffffff+1)

    def test_hostmask(self):
        m = Mask4(0xff)
        self.assertEqual(m.mask, 0xff)
        self.assertEqual(m.prefixlen, 0)
        self.assertEqual(~m, Mask4(0xffffff00))

        m = Mask6(0xff)
        self.assertEqual(m.mask, 0xff)
        self.assertEqual(m.prefixlen, 0)
        self.assertEqual(~m, Mask6(0xffffffffffffffffffffffffffffff00))

    def test_parsing(self):
        # Parsing v4
        m = Mask4('0xffffff00')
        self.assertEqual(m.mask, 0xffffff00)
        self.assertEqual(m.prefixlen, 24)

        m = Mask4('0xffffffff')
        self.assertEqual(m.mask, 0xffffffff)
        self.assertEqual(m.prefixlen, 32)

        m = Mask4('255.255.0.0')
        self.assertEqual(m.mask, 0xffff0000)
        self.assertEqual(m.prefixlen, 16)

        m = Mask4('255.255.255.255')
        self.assertEqual(m.mask, 0xffffffff)
        self.assertEqual(m.prefixlen, 32)

        m = Mask4('0.0.0.0')
        self.assertEqual(m.mask, 0x00000000)
        self.assertEqual(m.prefixlen, 0)

        m = Mask4('/32')
        self.assertEqual(m.mask, 0xffffffff)
        self.assertEqual(m.prefixlen, 32)

        m = Mask4('/1')
        self.assertEqual(m.mask, 0x80000000L)
        self.assertEqual(m.prefixlen, 1)
        m1 = Mask4('1')
        self.assertEqual(m.mask, m1.mask)
        self.assertEqual(m.prefixlen, m1.prefixlen)

        m = Mask6('/128')
        self.assertEqual(m.mask, 0xffffffffffffffffffffffffffffffff)
        self.assertEqual(m.prefixlen, 128)

        m = Mask6('/64')
        self.assertEqual(m.mask, 0xffffffffffffffff0000000000000000)
        self.assertEqual(m.prefixlen, 64)
        m1 = Mask6('64')
        self.assertEqual(m.mask, m1.mask)
        self.assertEqual(m.prefixlen, m1.prefixlen)


        self.assertRaises(MaskValidationError, Mask4, 'ffffffff')
        # Too many digits.
        self.assertRaises(MaskValidationError, Mask4, '0xfffffffff')
        # Not enough
        self.assertRaises(MaskValidationError, Mask4, '0xf')
        self.assertRaises(MaskValidationError, Mask4, '0x')
        self.assertRaises(MaskValidationError, Mask4, '1.2.3.4.5')
        self.assertRaises(MaskValidationError, Mask4, '1.2.3')
        self.assertRaises(MaskValidationError, Mask4, '/-1')
        self.assertRaises(MaskValidationError, Mask4, '/33')
        self.assertRaises(MaskValidationError, Mask6, '/129')

        # Parsing v6
        # Strings currently not supported.
        self.assertRaises(MaskValidationError, Mask6, '0xffffffffffffffff0000000000000000')

    def test_comparison(self):
        self.assertEqual(Mask4('0xffffffe0'), Mask4('0xffffffe0'))
        self.assertNotEqual(Mask4('0xffffffe0'), Mask4('0xffffffff'))
        self.assertNotEqual(Mask4('0xffffffff'), Mask6(0x000000000000000000000000ffffffff))

        self.assertTrue(Mask4('0xffffff00') < Mask4('0xffffffe0'))
        self.assertTrue(Mask4('0xffffffff') < Mask6(0x000000000000000000000000ffffffff))

        self.assertTrue(Mask4('0xffffffe0') <= Mask4('0xffffffe0'))
        self.assertTrue(Mask4('0xffffff00') <= Mask4('0xffffffe0'))
        self.assertTrue(Mask4('0xffffffff') <= Mask6(0x000000000000000000000000ffffffff))

        self.assertTrue(Mask4('0xffffffe0') > Mask4('0xffffff00'))
        self.assertTrue(Mask6(0x000000000000000000000000ffffffff) > Mask4('0xffffffff'))

        self.assertTrue(Mask4('0xffffffe0') >= Mask4('0xffffffe0'))
        self.assertTrue(Mask4('0xffffffe0') >= Mask4('0xffffff00'))
        self.assertTrue(Mask6(0x000000000000000000000000ffffffff) >= Mask4('0xffffffff'))

    def test_mask_to_prefixlen(self):
        self.assertEqual(Mask4.mask_to_prefixlen(0), 0)
        self.assertEqual(Mask4.mask_to_prefixlen(0xffff0000), 16)
        self.assertEqual(Mask4.mask_to_prefixlen(0xffffffff), 32)
        self.assertRaises(MaskValidationError, Mask4.mask_to_prefixlen, 0xff)
        self.assertRaises(MaskValidationError, Mask4.mask_to_prefixlen, -1)
        self.assertRaises(MaskValidationError, Mask4.mask_to_prefixlen, 0xffffffff+1)

        self.assertEqual(Mask6.mask_to_prefixlen(0), 0)
        self.assertEqual(Mask6.mask_to_prefixlen(0xffffffffffffffff0000000000000000), 64)
        self.assertEqual(Mask6.mask_to_prefixlen(0xffffffffffffffffffffffffffffffff), 128)
        self.assertRaises(MaskValidationError, Mask6.mask_to_prefixlen, 0xff)
        self.assertRaises(MaskValidationError, Mask6.mask_to_prefixlen, -1)
        self.assertRaises(MaskValidationError, Mask6.mask_to_prefixlen, 0xffffffffffffffffffffffffffffffff+1)

    def test_prefixlen_to_mask(self):
        self.assertEqual(Mask4.prefixlen_to_mask(0), 0)
        self.assertEqual(Mask4.prefixlen_to_mask(16), 0xffff0000)
        self.assertEqual(Mask4.prefixlen_to_mask(32), 0xffffffff)
        self.assertRaises(MaskValidationError, Mask4.prefixlen_to_mask, 0xff)
        self.assertRaises(MaskValidationError, Mask4.prefixlen_to_mask, -1)
        self.assertRaises(MaskValidationError, Mask4.prefixlen_to_mask, 33)

        self.assertEqual(Mask6.prefixlen_to_mask(0), 0)
        self.assertEqual(Mask6.prefixlen_to_mask(64), 0xffffffffffffffff0000000000000000)
        self.assertEqual(Mask6.prefixlen_to_mask(128), 0xffffffffffffffffffffffffffffffff)
        self.assertRaises(MaskValidationError, Mask6.prefixlen_to_mask, -1)
        self.assertRaises(MaskValidationError, Mask6.prefixlen_to_mask, 129)

    def test_is_netmask(self):
        self.assertTrue(Mask4(0).is_netmask())
        self.assertTrue(Mask4(0xffffff00).is_netmask())
        self.assertTrue(Mask4(0xffffffff).is_netmask())
        self.assertFalse(Mask4(0xff).is_netmask())
        self.assertFalse(Mask4(0xffffff).is_netmask())

        self.assertTrue(Mask6(0).is_netmask())
        self.assertTrue(Mask6(0xffffffffffffffff0000000000000000).is_netmask())
        self.assertTrue(Mask6(0xffffffffffffffffffffffffffffffff).is_netmask())
        self.assertFalse(Mask6(0xff).is_netmask())
        self.assertFalse(Mask6(0xffffff).is_netmask())

    def test_is_hostmask(self):
        self.assertTrue(Mask4(0xf).is_hostmask())
        self.assertTrue(Mask4(0xffffffff).is_hostmask())
        self.assertTrue(Mask4(0).is_hostmask())
        self.assertFalse(Mask4(0xffffff00).is_hostmask())

        self.assertTrue(Mask6(0xf).is_hostmask())
        self.assertTrue(Mask6(0xffffffff).is_hostmask())
        self.assertTrue(Mask6(0xffffffffffffffffffffffffffffffff).is_hostmask())
        self.assertTrue(Mask6(0).is_hostmask())
        self.assertFalse(Mask6(0xffffffffffffffff0000000000000000).is_hostmask())

    def test_format(self):
        m = Mask4(0)
        self.assertEqual(m.format(), '0x00000000')
        m = Mask4(1)
        self.assertEqual(m.format(), '0x00000001')
        # Bob wants this to be a prefix length.
        m = Mask4('1')
        self.assertEqual(m.format(), '1')
        m = Mask4('32')
        self.assertEqual(m.format(), '32')
        m = Mask4('255.255.255.255')
        self.assertEqual(m.format(), '255.255.255.255')
        m = Mask4('255.255.255.0')
        self.assertEqual(m.format(), '255.255.255.0')
        m = Mask4('0.0.0.0')
        self.assertEqual(m.format(), '0.0.0.0')
        m = Mask4('0xffffff00')
        self.assertEqual(m.format(), '0xffffff00')
        self.assertEqual(m.format(format=MASK_FORMAT.HEX), '0xffffff00')
        self.assertEqual(m.format(format=MASK_FORMAT.DOTTED_QUAD), '255.255.255.0')
        self.assertEqual(m.format(format=MASK_FORMAT.PREFIX), '24')

        m = Mask6(0)
        self.assertEqual(m.format(), '0x00000000000000000000000000000000')
        m = Mask6(1)
        self.assertEqual(m.format(), '0x00000000000000000000000000000001')
        m = Mask6('1')
        self.assertEqual(m.format(), '1')

if __name__ == '__main__':
    unittest.main()
