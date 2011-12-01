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

"""Unittests for range module."""

__version__ = '$Revision: #1 $'

import unittest

from aplib.net.ip import IPv4, IPv6, IPValidationError
from aplib.net.range import IPRange, Prefix, IPGlob

class Test(unittest.TestCase):

    def test_size(self):
        r = IPRange(IPv4('1.2.3.4'), IPv4('1.2.3.10'))
        self.assertEqual(r.size(), 7)

        r = IPRange(IPv4('0.0.0.0'), IPv4('255.255.255.255'))
        self.assertEqual(r.size(), 2**32)

        r = IPRange(IPv6('1::'), IPv6('2::'))
        self.assertEqual(r.size(), 2**112 + 1)

        r = IPGlob('1.2.3.4')
        self.assertEqual(r.size(), 1)

        r = Prefix('1.2.3.4')
        self.assertEqual(r.size(), 1)

        r = Prefix('2001:db8::/32')
        self.assertEqual(r.size(), 2**96)

    def test_getitem(self):
        # This also implicitly tests iterator().
        r = Prefix('1.2.3.0/24')
        self.assertEqual(r[0], IPv4('1.2.3.0'))
        self.assertEqual(r[-1], IPv4('1.2.3.255'))
        self.assertEqual(list(r[:5]), [IPv4('1.2.3.0'),
                                       IPv4('1.2.3.1'),
                                       IPv4('1.2.3.2'),
                                       IPv4('1.2.3.3'),
                                       IPv4('1.2.3.4'),
                                      ])
        self.assertEqual(list(r[254:]), [IPv4('1.2.3.254'), IPv4('1.2.3.255')])
        self.assertEqual(list(r[3:5]), [IPv4('1.2.3.3'), IPv4('1.2.3.4')])
        self.assertEqual(list(r[3:20:5]), [IPv4('1.2.3.3'),
                                           IPv4('1.2.3.8'),
                                           IPv4('1.2.3.13'),
                                           IPv4('1.2.3.18'),
                                          ])

        r = Prefix('2001:db8::/32')
        self.assertEqual(r[0], IPv6('2001:db8::'))
        self.assertEqual(r[-1], IPv6('2001:db8:ffff:ffff:ffff:ffff:ffff:ffff'))

    def test_contains(self):
        self.assertTrue(IPv4('1.2.3.4') in Prefix('1.2.3.0/24'))
        self.assertTrue(IPv4('1.2.3.0') in Prefix('1.2.3.0/24'))
        self.assertTrue(IPv4('1.2.3.255') in Prefix('1.2.3.0/24'))
        self.assertFalse(IPv4('1.2.4.1') in Prefix('1.2.3.0/24'))

        self.assertFalse(IPv6('::1.2.3.4') in Prefix('1.2.3.0/24'))

    def test_is_subnet(self):
        self.assertTrue(Prefix('1.2.3.0/27').is_subnet(Prefix('1.2.3.0/24')))
        self.assertFalse(Prefix('1.2.3.0/16').is_subnet(Prefix('1.2.0.0/24')))

    def test_is_supernet(self):
        self.assertFalse(Prefix('1.2.3.0/27').is_supernet(Prefix('1.2.3.0/24')))
        self.assertTrue(Prefix('1.2.3.0/16').is_supernet(Prefix('1.2.0.0/24')))

    def test_ipglob(self):
        expected = [
            ('1.2.3.4', '1.2.3.4', '1.2.3.4'),
            ('1.2.3',   '1.2.3.0', '1.2.3.255'),
            ('1.2',     '1.2.0.0', '1.2.255.255'),
            ('1',       '1.0.0.0', '1.255.255.255'),
            ('1.2.3.*', '1.2.3.0', '1.2.3.255'),
            ('1.2.*.*', '1.2.0.0', '1.2.255.255'),
            ('1.*.*.*', '1.0.0.0', '1.255.255.255'),
            ('*.*.*.*', '0.0.0.0', '255.255.255.255'),
            ('1.2.*',   '1.2.0.0', '1.2.255.255'),
            ('1.*.*',   '1.0.0.0', '1.255.255.255'),
            ('1.*',     '1.0.0.0', '1.255.255.255'),
            ('*.*.*.*', '0.0.0.0', '255.255.255.255'),
            ('*.*.*',   '0.0.0.0', '255.255.255.255'),
            ('*.*',     '0.0.0.0', '255.255.255.255'),
            ('*',       '0.0.0.0', '255.255.255.255'),
            ('1.2.3.4-10', '1.2.3.4', '1.2.3.10'),
            ('1.2.3-6', '1.2.3.0', '1.2.6.255'),
            ('1.2-5',   '1.2.0.0', '1.5.255.255'),
            ('1-3',     '1.0.0.0', '3.255.255.255'),
            ('1.2.3-6.*','1.2.3.0', '1.2.6.255'),
            ('1.2-5.*.*','1.2.0.0', '1.5.255.255'),
            ('1-3.*.*.*','1.0.0.0', '3.255.255.255'),
        ]

        for value, first, last in expected:
            if value.count('.') != 3:
                values = [value, value+'.']
            else:
                values = [value]
            for value in values:
                g = IPGlob(value)
                self.assertEqual(g.first, IPv4(first))
                self.assertEqual(g.last, IPv4(last))

        invalid = [
            '2001:db8::/32',
            '::1.2.3.4',
            '1.2.3.4.5',
            '1..',
            '1...',
            '1....',
            '.',
            '..',
            '...',
            '....',
            'foo',
            '1.2.3.256',
            '1.2.*.4',
            '1-2.4.*.*',
        ]
        for value in invalid:
            self.assertRaises(IPValidationError, IPGlob, value)

    def test_comparison(self):
        expected_eq = [
            ('1.2.3.4', '1.2.3.4'),
            ('1.0.0.0/8', '1.0.0.0/8'),
            ('0.0.0.0', '0.0.0.0'),
            ('255.255.255.255', '255.255.255.255'),
            ('::', '::'),
        ]

        for a, b in expected_eq:
            ra = Prefix(a)
            rb = Prefix(b)
            self.assertTrue(ra == rb)
            self.assertTrue(ra <= rb)
            self.assertTrue(ra >= rb)
            self.assertFalse(ra != rb)
            self.assertFalse(ra < rb)
            self.assertFalse(ra > rb)

        expected_lt = [
            ('1.0.0.0/8', '2.0.0.0/8'),
            ('1.0.0.0/8', '1.0.0.0/16'),
            ('1.0.0.0/8', '1.192.0.0/10'),
            ('1.0.0.0/8', '1.64.0.0/10'),
            ('1.2.3.0-9', '1.2.3.5-14'),
            ('1.2.3.0-9', '1.2.3.5-100'),
        ]

        for a, b in expected_lt:
            if '-' in a:
                ra = IPGlob(a)
            else:
                ra = Prefix(a)
            if '-' in b:
                rb = IPGlob(b)
            else:
                rb = Prefix(b)
            self.assertTrue(ra < rb)
            self.assertTrue(ra <= rb)
            self.assertTrue(ra != rb)
            self.assertFalse(ra > rb)
            self.assertFalse(ra >= rb)
            self.assertFalse(ra == rb)

    def test_adjacent(self):
        self.assertTrue(Prefix('1.0.0.0/8').is_adjacent(Prefix('2.0.0.0/8')))
        self.assertFalse(Prefix('1.0.0.0/8').is_adjacent(Prefix('1.0.0.0/8')))
        self.assertFalse(Prefix('1.0.0.0/8').is_adjacent(Prefix('::2.0.0.0/88')))
        self.assertTrue(Prefix('1.2.3.4').is_adjacent(Prefix('1.2.3.5')))

    def test_overlaps(self):
        self.assertTrue(Prefix('1.0.0.0/24').overlaps(Prefix('1.0.0.0/8')))
        self.assertTrue(Prefix('1.0.0.0/8').overlaps(Prefix('1.0.0.0/24')))
        self.assertTrue(Prefix('1.2.3.4').overlaps(Prefix('1.2.3.4')))
        self.assertTrue(Prefix('::').overlaps(Prefix('::')))

if __name__ == '__main__':
    unittest.main()
