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

__version__ = '$Revision: #8 $'

import unittest

from aplib.net.ip import (IP, IPv4, IPv6,
                          IPValidationError, MaskValidationError,
                          Mask4, Mask6, htop, ptoh, is_ip, is_ipv4, is_ipv6, is_cidr
                         )
from aplib.net.range import Prefix
import pickle

valid_ips = ['1.1.1.1', '2.2.2.0', '0.0.0.0', '255.255.255.255', '1.12.0.0',
             '::', '::', '1::2', '2::1', 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff','3::0']
valid_v4_cidrs = ['1.1.1.0/24', '1.0.0.0/8', '1.1.1.1/32']
valid_v6_cidrs = ['1::/64', 'ffff:ffff:ffff:ffff:ffff:ffff:ffff::/120',
                  '1::/16', '23:3::/64']

def is_exc(v):
    return isinstance(v, type) and issubclass(v, Exception) or isinstance(v, Exception)

class Test(unittest.TestCase):

    def test_parse_ipv4(self):
        expected = {
            '':                 IPValidationError,
        '\0':               IPValidationError,
            '.':                IPValidationError,
            '..':               IPValidationError,
            '...':              IPValidationError,
            '....':             IPValidationError,
            '0':                IPValidationError,
            '1':                IPValidationError,
            '1.':               IPValidationError,
            '1.2':              IPValidationError,
            '1.2.':             IPValidationError,
            '1.2.3':            IPValidationError,
            '1.2.3.':           IPValidationError,
            '0.0.0.0':          0,
            '1.2.3.4':          0x01020304,
            '255.255.255.255':  0xffffffff,
            '256.256.256.256':  IPValidationError,
            '001.002.003.004':  (0x01020304, '1.2.3.4'),
        }
        self._test_parse(expected, IPv4)
        self._test_convert(expected, is_ipv4)

    def test_parse_ipv6(self):
        expected = {
            '':                 IPValidationError,
            '\0':               IPValidationError,
            ':':                IPValidationError,
            ':1':               IPValidationError,
            ':::':              IPValidationError,
            'foo':              IPValidationError,
            '1:2:3:4:5:6:7':    IPValidationError,
            '1:2:3:4:5:6:7:':   IPValidationError,
            ':2:3:4:5:6:7:8':   IPValidationError,
            '1:2:3:4:5:6:7:8:9':IPValidationError,
            '1:2:3:4::5:6:7:8:9':IPValidationError,
            '1::2::3':          IPValidationError,
            '1:::2':            IPValidationError,
            '12345':            IPValidationError,
            '1234':             IPValidationError,
            '1234::12345':      IPValidationError,
            '1:2:3:12345:5:6:7:8':  IPValidationError,
            'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff': 0xffffffffffffffffffffffffffffffff,
            '1234:5678:90ab:cdef:1234:5678:90ab:cdef': (0x1234567890abcdef1234567890abcdef, '1234:5678:90ab:cdef:1234:5678:90ab:cdef'),
            '0000:0000:0000:0000:0000:0000:0000:0000':  (0, '::'),
            '0001:0002:0003:0004:0005:0006:0007:0008':  (0x00010002000300040005000600070008, '1:2:3:4:5:6:7:8'),
            '1:2:3:4:5:6:7:8':  0x00010002000300040005000600070008,
            '0:0:0:0:0:0:0:1':  (1, '::1'),
            '2001:DB8::8:800:200C:417A':    0x20010db80000000000080800200c417a,
            'FF01::101':        0xff010000000000000000000000000101,
            '::':               0,
            '1::':              0x00010000000000000000000000000000,
            '::1':              1,
            '::ffff':           0xffff,
            '::ffff:1.2.3.4':   0xffff01020304,
            '::0.0.0.0':        (0, '::'),
            '::255.255.255.255':0xffffffff,
            '::ffff:255.255.255.255': 0xffffffffffff,
            '::ffff:0.0.0.0':   0xffff00000000,
            '::1.2.3.4':        0x1020304,
            '::ffff:5.6.7.8':   0xffff05060708,
            '1:2:3:4:5:6:1.2.3.4': (0x10002000300040005000601020304, '1:2:3:4:5:6:102:304'),
        }
        self._test_convert(expected, is_ipv6)
        expected['1.2.3.4'] = IPValidationError
        self._test_parse(expected, IPv6)

    def _test_parse(self, expected, ip):

        for value, output in expected.items():
            if isinstance(output, tuple):
                output, rendered_output = output
            else:
                rendered_output = value.lower()
            for value in (value.lower(), value.upper()):
                if is_exc(output):
                    self._raises(ip.parse_ip, value, output)
                else:
                    self._equal(ip.parse_ip, value, output)
                    x = ip(value)
                    self.assertEqual(int(x), output)
                    self.assertEqual(x.format(), rendered_output)
                    self.assertEqual(x.prefixlen, ip.WIDTH)
                    self.assertEqual(int(x.netmask), ip.FULL_MASK)
                    self._equal(ip.int_to_str, output, rendered_output)
                self._raises(ip.parse_ip, value+'!', IPValidationError)
                self._raises(ip, -1, IPValidationError)
                self._raises(ip, ip.FULL_MASK+1, IPValidationError)
                for x in xrange(ip.WIDTH+1):
                    v = '%s/%i' % (value, x)
                    if is_exc(output):
                        self._raises(ip.parse_ip_prefix, v, output)
                    else:
                        self._equal(ip.parse_ip_prefix, v, (output, x))
                self._raises(ip.parse_ip_prefix, '%s/' % value, IPValidationError)
                self._raises(ip.parse_ip_prefix, '%s/%i' % (value, ip.WIDTH+1), IPValidationError)
                self._raises(ip.parse_ip_prefix, '%s/a' % value, IPValidationError)

    def _test_convert(self, expected, ip_check):
        for value, output in expected.items():
            if isinstance(output, tuple):
                output, rendered_output = output
            else:
                rendered_output = value.lower()
            for value in (value.lower(), value.upper()):
                if is_exc(output):
                    self.assertFalse(ip_check(value))
                    self._raises(ptoh, value, output)
                else:
                    self.assertTrue(ip_check(value))
                    self._equal(ptoh, value, output)

    def _equal(self, func, v, o):
        try:
            result = func(v)
            if not result == o:
                self.fail('%r != %r' % (result, o))
        except AssertionError:
            raise
        except Exception, e:
            self.fail('Input of %r raised exception when expected value %r: %s' % (v, o, e))

    def _raises(self, func, v, o):
        try:
            result = func(v)
        except o:
            return
        else:
            self.fail('Input of %r expected to raise %s, instead returned %r' % (v, o, result))

    def test_int_to_str(self):
        self.assertRaises(IPValidationError, IPv4.int_to_str, -1)
        self.assertRaises(IPValidationError, IPv6.int_to_str, -1)

        self.assertRaises(IPValidationError, IPv4.int_to_str, 2**32)
        self.assertRaises(IPValidationError, IPv6.int_to_str, 2**128)

    def test_explicit_netmask(self):
        x = IPv4('1.2.3.4', netmask='0xffffff00')
        self.assertEqual(int(x.netmask), 0xffffff00)
        self.assertEqual(x.prefixlen, 24)

        x = IPv4('1.2.3.4', netmask=0xffffff00)
        self.assertEqual(int(x.netmask), 0xffffff00)
        self.assertEqual(x.prefixlen, 24)

        x = IPv4('1.2.3.4', netmask=0)
        self.assertEqual(int(x.netmask), 0)
        self.assertEqual(x.prefixlen, 0)

        x = IPv4('1.2.3.4', netmask='0xffffffff')
        self.assertEqual(int(x.netmask), 0xffffffff)
        self.assertEqual(x.prefixlen, 32)

        x = IPv4('1.2.3.4', netmask='255.255.255.0')
        self.assertEqual(int(x.netmask), 0xffffff00)
        self.assertEqual(x.prefixlen, 24)

        mask = Mask4('255.255.0.0')
        x = IPv4('1.2.3.4', netmask=mask)
        self.assertEqual(int(x.netmask), 0xffff0000)
        self.assertEqual(x.prefixlen, 16)

        x = IPv4(0x01020304, netmask='0xffffff00')
        self.assertEqual(int(x.netmask), 0xffffff00)
        self.assertEqual(x.prefixlen, 24)

        self.assertRaises(MaskValidationError, IPv4, '1.2.3.4', netmask='foo')
        self.assertRaises(MaskValidationError, IPv4, '1.2.3.4/24', netmask='255.255.255.0')
        self.assertRaises(MaskValidationError, IPv4, '1.2.3.4', netmask=Mask6(0))
        self.assertRaises(MaskValidationError, IPv4, '1.2.3.4', netmask=-1)
        self.assertRaises(MaskValidationError, IPv4, '1.2.3.4', netmask=0xffffffff+1)
        # Hostmask not allowed.
        self.assertRaises(MaskValidationError, IPv4, '1.2.3.4', netmask=Mask4(0xff))

        ######################################################################

        x = IPv6('1:2:3:4:5:6:7:8', netmask=0xffffffffffffffff0000000000000000)
        self.assertEqual(int(x.netmask), 0xffffffffffffffff0000000000000000)
        self.assertEqual(x.prefixlen, 64)

        x = IPv6('1:2:3:4:5:6:7:8', netmask=0)
        self.assertEqual(int(x.netmask), 0)
        self.assertEqual(x.prefixlen, 0)

        x = IPv6('1:2:3:4:5:6:7:8', netmask=0xffffffffffffffffffffffffffffffff)
        self.assertEqual(int(x.netmask), 0xffffffffffffffffffffffffffffffff)
        self.assertEqual(x.prefixlen, 128)

        mask = Mask6(0xffffffffffffffffffffffff00000000)
        x = IPv6('1:2:3:4:5:6:7:8', netmask=mask)
        self.assertEqual(int(x.netmask), 0xffffffffffffffffffffffff00000000)
        self.assertEqual(x.prefixlen, 96)

        x = IPv6(0x0102030405060708, netmask=0xffffffffffff00000000000000000000)
        self.assertEqual(int(x.netmask), 0xffffffffffff00000000000000000000L)
        self.assertEqual(x.prefixlen, 48)

        self.assertRaises(MaskValidationError, IPv6, '1:2:3:4:5:6:7:8', netmask='foo')
        self.assertRaises(MaskValidationError, IPv6, '1:2:3:4:5:6:7:8/64', netmask=0xffffffffffffffff0000000000000000)
        self.assertRaises(MaskValidationError, IPv6, '1:2:3:4:5:6:7:8', netmask=Mask4(0))
        self.assertRaises(MaskValidationError, IPv6, '1:2:3:4:5:6:7:8', netmask=-1)
        self.assertRaises(MaskValidationError, IPv6, '1:2:3:4:5:6:7:8', netmask=0xffffffffffffffffffffffffffffffff+1)
        # Strings currently not supported.
        self.assertRaises(MaskValidationError, IPv6, '1:2:3:4:5:6:7:8', netmask='0xffffffffffffffff0000000000000000')
        # Hostmask not allowed.
        self.assertRaises(MaskValidationError, IPv6, '1:2:3:4:5:6:7:8', netmask=Mask6(0xff))

    def test_format(self):
        # Most format tests taken care of by test_parse.
        self.assertEqual(IPv4('1.2.3.4').format(), '1.2.3.4')
        self.assertEqual(IPv4('1.2.3.4').format(always_prefix=True), '1.2.3.4/32')
        self.assertEqual(IPv4('1.2.3.4/31').format(), '1.2.3.4/31')

        self.assertEqual(IPv6('1:2:3:4:5:6:7:8').format(), '1:2:3:4:5:6:7:8')
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8').format(always_prefix=True), '1:2:3:4:5:6:7:8/128')
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/127').format(), '1:2:3:4:5:6:7:8/127')

    def test_network(self):
        self.assertEqual(IPv4('1.2.3.4/32').network, Prefix('1.2.3.4/32'))
        self.assertEqual(IPv4('1.2.3.4/24').network, Prefix('1.2.3.0/24'))
        self.assertEqual(IPv4('1.2.3.4/0').network, Prefix('0.0.0.0/0'))

        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/128').network, Prefix('1:2:3:4:5:6:7:8'))
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/64').network, Prefix('1:2:3:4::/64'))
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/0').network, Prefix('::/0'))

    def test_netmask(self):
        self.assertEqual(IPv4('1.2.3.4/32').netmask, Mask4(0xffffffff))
        self.assertEqual(IPv4('1.2.3.4/24').netmask, Mask4(0xffffff00))
        self.assertEqual(IPv4('1.2.3.4/0').netmask, Mask4(0))
        self.assertEqual(IPv4('1.2.3.4/24').netmask, IP('1.2.3.4', '24').netmask)

        self.assertEqual(IPv4('1.2.3.4/32').netmask_int, 0xffffffff)
        self.assertEqual(IPv4('1.2.3.4/32').netmask_int, IP('1.2.3.4', '32').netmask_int)
        self.assertEqual(IPv4('1.2.3.4/24').netmask_int, 0xffffff00)
        self.assertEqual(IPv4('1.2.3.4/0').netmask_int, 0)

        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/128').netmask, Mask6(0xffffffffffffffffffffffffffffffff))
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/128').netmask, IP('1:2:3:4:5:6:7:8', '128').netmask)
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/64').netmask, Mask6(0xffffffffffffffff0000000000000000))
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/0').netmask, Mask6(0))

        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/128').netmask_int, 0xffffffffffffffffffffffffffffffff)
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/64').netmask_int, 0xffffffffffffffff0000000000000000)
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/64').netmask_int, IP('1:2:3:4:5:6:7:8', '64').netmask_int)
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/0').netmask_int, 0)

    def test_hostmask(self):
        self.assertEqual(IPv4('1.2.3.4/32').hostmask, Mask4(0))
        self.assertEqual(IPv4('1.2.3.4/24').hostmask, Mask4(0xff))
        self.assertEqual(IPv4('1.2.3.4/0').hostmask, Mask4(0xffffffff))

        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/128').hostmask, Mask6(0))
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/64').hostmask, Mask6(0x0000000000000000ffffffffffffffff))
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/0').hostmask, Mask6(0xffffffffffffffffffffffffffffffff))

    def test_broadcast(self):
        self.assertEqual(IPv4('1.2.3.4/32').broadcast, IPv4('1.2.3.4'))
        self.assertEqual(IPv4('1.2.3.4/24').broadcast, IPv4('1.2.3.255'))
        self.assertEqual(IPv4('1.2.3.4/0').broadcast, IPv4('255.255.255.255'))

        # Broadcast doesn't really make sense in IPv6.
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/128').broadcast, IPv6('1:2:3:4:5:6:7:8'))
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/64').broadcast, IPv6('1:2:3:4:ffff:ffff:ffff:ffff'))
        self.assertEqual(IPv6('1:2:3:4:5:6:7:8/0').broadcast, IPv6('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'))

    def test_comparison(self):
        self.assertEqual(IPv4('1.2.3.4'), IPv4('1.2.3.4'))
        self.assertEqual(IPv4('1.2.3.4/24'), IPv4('1.2.3.4/24'))
        self.assertNotEqual(IPv4('1.2.3.4'), IPv4('1.2.3.5'))
        self.assertNotEqual(IPv4('1.2.3.4/24'), IPv4('1.2.3.4/32'))
        self.assertNotEqual(IPv4('1.2.3.4'), IPv6('::1.2.3.4'))

        self.assertTrue(IPv4('1.2.3.0') < IPv4('1.2.3.4'))
        self.assertTrue(IPv4('1.2.3.4/16') < IPv4('1.2.3.4/24'))
        self.assertTrue(IPv4('1.2.3.4') < IPv6('::1.2.3.4'))
        self.assertFalse(IPv4('1.2.4.0') < IPv4('1.2.3.4'))

        self.assertTrue(IPv4('1.2.3.4') <= IPv4('1.2.3.4'))
        self.assertTrue(IPv4('1.2.3.4/24') <= IPv4('1.2.3.4/24'))
        self.assertTrue(IPv4('1.2.3.0') <= IPv4('1.2.3.4'))
        self.assertTrue(IPv4('1.2.3.4/16') <= IPv4('1.2.3.4/24'))
        self.assertTrue(IPv4('1.2.3.4') <= IPv6('::1.2.3.4'))
        self.assertFalse(IPv4('1.2.4.0') <= IPv4('1.2.3.4'))

        self.assertTrue(IPv4('1.2.3.4') > IPv4('1.2.3.0'))
        self.assertTrue(IPv4('1.2.3.4/24') > IPv4('1.2.3.4/16'))
        self.assertTrue(IPv6('::1.2.3.4') > IPv4('1.2.3.4'))
        self.assertFalse(IPv4('1.2.3.0') > IPv4('1.2.4.0'))

        self.assertTrue(IPv4('1.2.3.4') >= IPv4('1.2.3.4'))
        self.assertTrue(IPv4('1.2.3.4/24') >= IPv4('1.2.3.4/24'))
        self.assertTrue(IPv4('1.2.3.4') >= IPv4('1.2.3.0'))
        self.assertTrue(IPv4('1.2.3.4/24') >= IPv4('1.2.3.4/16'))
        self.assertTrue(IPv6('::1.2.3.4') >= IPv4('1.2.3.4'))
        self.assertFalse(IPv4('1.2.3.0') >= IPv4('1.2.4.0'))

    def _test_is(self, method, yes, no):
        for value in yes:
            i = IP(value)
            self.assertTrue(getattr(i, method)())
        for value in no:
            i = IP(value)
            self.assertFalse(getattr(i, method)())

    def test_is_private(self):
        yes = ['10.0.0.0', '10.1.2.3', '10.255.255.255',
               '172.16.0.0', '172.31.255.255',
               '192.168.0.0', '192.168.255.255',
               'fc00::', 'fdff:ffff:ffff:ffff:ffff:ffff:ffff:ffff']
        no = ['1.2.3.4', '0.0.0.0', '255.255.255.255',
              '17.15.255.255', '127.0.0.1',
              '192.0.2.0', '239.192.0.0',
              '::', '::10.0.0.0', 'fec0::', '::1']
        self._test_is('is_private', yes, no)

    def test_is_multicast(self):
        yes = ['224.0.0.0', '239.255.255.255',
               'ff00::', 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff']
        no = ['240.0.0.0', '127.0.0.1', '0.0.0.0', '255.255.255.255',
              '2001:db8::', '::', '::224.0.0.0', '::1']
        self._test_is('is_multicast', yes, no)

    def test_is_loopback(self):
        yes = ['127.0.0.0', '127.0.0.1', '127.255.255.255',
               '::1']
        no = ['128.0.0.0', '0.0.0.0', '255.255.255.255',
              '::', '2001:db8::']
        self._test_is('is_loopback', yes, no)

    def test_is_unspecified(self):
        yes = ['0.0.0.0', '::']
        no = ['127.0.0.1', '0.0.0.1', '::1']
        self._test_is('is_unspecified', yes, no)

    def test_is_link_local(self):
        yes = ['169.254.0.0', '169.254.255.255',
               'fe80::', 'febf:ffff:ffff:ffff:ffff:ffff:ffff:ffff']
        no = ['127.0.0.1', '169.255.0.0', '224.0.0.0', '10.0.0.0',
              '::', '::1', 'ff00::', 'fc00::']
        self._test_is('is_link_local', yes, no)

    def test_forward_dns_rr_type(self):
        self.assertEqual(IP('::1').forward_dns_rr_type, 'AAAA')
        self.assertEqual(IP('127.0.0.1').forward_dns_rr_type, 'A')

    def test_reverse_dns(self):
        expected = [
            ('127.0.0.1', '1.0.0.127.in-addr.arpa'),
            ('0.0.0.0', '0.0.0.0.in-addr.arpa'),
            ('255.255.255.255', '255.255.255.255.in-addr.arpa'),
            ('1.2.3.4', '4.3.2.1.in-addr.arpa'),
            ('::', '0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa'),
            ('2001:db8::', '0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa'),
            ('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff', 'f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.f.ip6.arpa'),
        ]
        for value, output in expected:
            i = IP(value)
            self.assertEqual(i.reverse_dns(), output)

    def test_reverse_dns_pieces(self):
        # This test is purposely short because test_reverse_dns() implicitly tests this.
        expected = [
            ('1.2.3.4', '4.3.2.1'),
            ('123.234.56.67', '67.56.234.123'),
            ('2001:db8::', '0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2'),
            ('1234:5678:9abc:def0::', '0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.f.e.d.c.b.a.9.8.7.6.5.4.3.2.1'),
        ]
        for value, output in expected:
            i = IP(value)
            self.assertEqual(i.reverse_dns_pieces(), output)

        for value, output in expected:
            i = IP(value)
            self.assertEqual(i.reverse_dns_pieces('suffix'), output + '.suffix')

    def test_hex(self):
        expected = [
            ('1.2.3.4', '0x01020304'),
            ('0.0.0.0', '0x00000000'),
            ('255.255.255.255', '0xffffffff'),
            ('::', '0x00000000000000000000000000000000'),
            ('2001:db8::', '0x20010db8000000000000000000000000'),
        ]

        for value, output in expected:
            self.assertEqual(hex(IP(value)), output)

    def test_add(self):
        add_e = [
            ('1.2.3.4', 1, '1.2.3.5'),
            ('0.0.0.0', 255, '0.0.0.255'),
            ('1.2.3.0', IPv4('0.0.0.255'), '1.2.3.255'),
            ('1.2.3.0', -1, '1.2.2.255'),
            ('::', 1, '::1'),
            ('1:2:3:4::', IPv6('::5:6:7:8'), '1:2:3:4:5:6:7:8'),
            ('2001:db8::', -1, '2001:db7:ffff:ffff:ffff:ffff:ffff:ffff'),

        ]
        for value, diff, output in add_e:
            i = IP(value)
            p = i + diff
            self.assertEqual(p, IP(output))

        invalid = [
            ('0.0.0.0', -1),
            ('255.255.255.255', 1),
            ('::', -1),
            ('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff', 1),
        ]
        for value, diff in invalid:
            i = IP(value)
            self.assertRaises(IPValidationError, lambda: i+diff)

    def test_sub(self):
        sub_e = [
            ('1.2.3.4', 1, '1.2.3.3'),
            ('255.255.255.255', 255, '255.255.255.0'),
            ('1.2.3.0', IPv4('0.0.0.255'), '1.2.2.1'),
            ('1.2.3.0', -1, '1.2.3.1'),
            ('::1', 1, '::'),
            ('1:2:3:4:5:6:7:8', IPv6('::5:6:7:8'), '1:2:3:4::'),
            ('2001:db8::', -1, '2001:db8::1'),
        ]
        for value, diff, output in sub_e:
            i = IP(value)
            p = i - diff
            self.assertEqual(p, IP(output))

        invalid = [
            ('0.0.0.0', 1),
            ('255.255.255.255', -1),
            ('::', 1),
            ('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff', -1),
        ]
        for value, diff in invalid:
            i = IP(value)
            self.assertRaises(IPValidationError, lambda: i-diff)

    def test_localhost(self):
        self.assertEqual(IPv4.localhost, IPv4('127.0.0.1'))
        self.assertEqual(IPv6.localhost, IPv6('::1'))

    def test_subnet(self):
        self.assertEqual(IPv4('1.2.3.4').subnet(), [IPv4('1.2.3.4')])
        self.assertEqual(IPv4('1.2.3.4/8').subnet(),
                            [IPv4('1.0.0.0/9'), IPv4('1.128.0.0/9')])
        self.assertEqual(IPv4('1.2.3.4/8').subnet(2),
                            [IPv4('1.0.0.0/10'), IPv4('1.64.0.0/10'),
                             IPv4('1.128.0.0/10'), IPv4('1.192.0.0/10')])

        self.assertEqual(IPv6('::').subnet(), [IPv6('::')])
        self.assertEqual(IPv6('2001:db8::/32').subnet(),
                            [IPv6('2001:db8::/33'), IPv6('2001:db8:8000::/33')])

    def test_conversion(self):
       ips = ['0.0.0.0', '1.2.3.4', '192.168.0.0', '255.255.255.255',
              '::', '1::2', '1234:5678:90ab:cdef:1234:5678:90ab:cdef',
              '1::3', 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff']
       ipn = [0, 16909060, 3232235520L, 4294967295L, 0,
              5192296858534827628530496329220098L,
              24197857200151252728969465429440056815L,
              5192296858534827628530496329220099L,
              340282366920938463463374607431768211455L]
       for ip, packed_ip in zip(ips, ipn):
           self.assertEqual(ptoh(ip), packed_ip)
           if ip != '::':
               self.assertEqual(ip, htop(packed_ip))

    def test_is_ip(self):
        invalid_ips = ['', '.', '\0', '-1', 'asd', '1.1.1', '2.2.2.', '1.1.1.1/', '1.1.1.1/33',
                       ':::', '1::2::2', '1:2:3:4:5:6:7:8:9', '::/129', '2::1/', '2::1/-1',
                       '1212', '...', '.....', '1.1.1.-1', '23::fg', '32344::3', '43434/22',
                       '/', '//', '/30', '/129', '2/2/2', ':::/64']
        for ip in invalid_ips:
            self.assertFalse(is_ip(ip))
            self.assertFalse(is_ipv4(ip))
            self.assertFalse(is_ipv6(ip))

        valid_cidrs = valid_v4_cidrs + valid_v6_cidrs

        for ip in valid_ips:
            self.assertTrue(is_ip(ip))
            self.assertTrue(is_cidr(ip))
            self.assertFalse(is_cidr(ip, accept_ip=False))

        for ip in valid_cidrs:
            self.assertTrue(is_cidr(ip))
            self.assertFalse(is_ip(ip))
        for ip in valid_v4_cidrs:
            self.assertTrue(is_cidr(ip, version=4))
            self.assertFalse(is_cidr(ip, version=6))
        for ip in valid_v6_cidrs:
            self.assertTrue(is_cidr(ip, version=6))
            self.assertFalse(is_cidr(ip, version=4))

    def test_pickle(self):
        for ip in valid_ips:
            self.assertEqual(IP(ip), pickle.loads(pickle.dumps(IP(ip))))
        valid_cidrs = valid_v4_cidrs + valid_v6_cidrs
        for ip in valid_cidrs:
            self.assertEqual(IP(ip), pickle.loads(pickle.dumps(IP(ip))))

if __name__ == '__main__':
    unittest.main()
