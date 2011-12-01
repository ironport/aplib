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


"""Unittests for aplib.net.interface module."""

__version__ = '$Revision: #2 $'

import errno
import re
import socket
import subprocess
import sys
import unittest

from aplib.net.interface import name_to_index, get_flags, IN6_IFF
import aplib.oserrors

class Test(unittest.TestCase):

    def test_name_to_index(self):
        # This test relies on the fact that ifconfig returns interfaces in
        # sequential order according to their interface index.

        ifconfig = subprocess.Popen(['/sbin/ifconfig'], stdout=subprocess.PIPE)
        expected_if_idx = 0
        for line in ifconfig.stdout.readlines():
            m = re.search('^(\w+\d):', line)
            if m:
                expected_if_idx += 1
                if_name = m.group(1)
                if_idx = name_to_index(if_name)
                self.assertNotEquals(if_idx, 0,
                    msg='Error looking up interface index for %s' %(if_name))
                self.assertEquals(if_idx, expected_if_idx,
                    msg='Interface index for %s was %d, expected %d' %(
                        if_name, if_idx, expected_if_idx))
        self.assertNotEquals(expected_if_idx, 0,
            msg="Couldn't find any interfaces to test")

        self.assertRaises(aplib.oserrors.ENXIO, name_to_index, 'invalidinterface')

    def test_get_flags(self):
        # This is a nice test in that it validates our results against ifconfig.
        # Unfortunately, most systems won't have any of these flags set. Without
        # running this test as root I can't attempt to put the machine into any
        # of these states either.
        # On most systems this test simply verifies that the get_flags() call
        # isn't completely broken. It doesn't really verify that it's working.
        # If you're working on the get_flags call you should make a better
        # effort to put your interfaces into some of these states and check
        # the results. In particular duplicated is easy to check.

        try:
            s6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        except socket.error, e:
            if e.args[0] == errno.EPROTONOSUPPORT:
                sys.stderr.write('Warning: No IPv6 support; skipping tests\n')
                return
            raise

        # Maps ifconfig output to flag values
        ifconfig_states = {
            'anycast': IN6_IFF.IN6_IFF_ANYCAST,
            'tentative': IN6_IFF.IN6_IFF_TENTATIVE,
            'duplicated': IN6_IFF.IN6_IFF_DUPLICATED,
            'detached': IN6_IFF.IN6_IFF_DETACHED,
            'deprecated': IN6_IFF.IN6_IFF_DEPRECATED,
            'autoconf': IN6_IFF.IN6_IFF_AUTOCONF,
            'temporary': IN6_IFF.IN6_IFF_TEMPORARY,
        }

        ifconfig = subprocess.Popen(['/sbin/ifconfig'], stdout=subprocess.PIPE)
        if_name = ""
        addresses_tested = 0
        for line in ifconfig.stdout.readlines():
            m = re.search('^(\w+\d):', line)
            if m:
                if_name = m.group(1)
            addr_re = 'inet6 ([^ ]+)'
            m = re.search(addr_re, line)
            if m:
                addr = m.group(1)
                if addr.find('%') > -1:
                    addr = addr[:addr.find('%')]
                flags = get_flags(if_name, addr)
                for ifconfig_state in ifconfig_states:
                    if line.find(ifconfig_state) > -1:
                        self.assertNotEquals(flags & ifconfig_states[ifconfig_state], 0)
                addresses_tested += 1

        self.assertNotEquals(addresses_tested, 0)

if __name__ == '__main__':
    unittest.main()
