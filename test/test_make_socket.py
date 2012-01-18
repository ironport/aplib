import socket
import sys
import unittest

import aplib
import coro
import coro_unittest

class Test(unittest.TestCase):

    def test_make_socket_for_ip(self):
        if coro.has_ipv6():
            sock = aplib.make_socket_for_ip('2001::1', socket.SOCK_STREAM)
            self.assertEquals(sock.domain, socket.AF_INET6)
            sock = aplib.make_socket_for_ip('::', socket.SOCK_STREAM)
            self.assertEquals(sock.domain, socket.AF_INET6)
        else:
            sys.stderr.write('Warning: No IPv6 support; skipping tests\n')

        sock = aplib.make_socket_for_ip('1.2.3.4', socket.SOCK_STREAM)
        self.assertEquals(sock.domain, socket.AF_INET)
        sock = aplib.make_socket_for_ip('0.0.0.0', socket.SOCK_STREAM)
        self.assertEquals(sock.domain, socket.AF_INET)

        self.assertRaises(ValueError, aplib.make_socket_for_ip, '123', 0)

if __name__ == '__main__':
    coro_unittest.run_tests()
