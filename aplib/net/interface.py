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

# $Header: //prod/main/ap/aplib/aplib/net/interface.py#2 $

"""Interface helper methods."""

__version__ = '$Revision: #2 $'

import fcntl
import socket
import struct

from aplib.net import _net

name_to_index = _net.if_name_to_index

# http://code.activestate.com/recipes/415903-two-dict-classes-which-can-lookup-keys-by-value-an/
# PSF license

class ReverseDict(dict):
    """
    A dictionary which can lookup values by key, and keys by value.
    All values and keys must be hashable, and unique.
    """
    def __init__(self, *args, **kw):
        dict.__init__(self, *args, **kw)
        self.reverse = dict((reversed(list(i)) for i in self.items()))

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.reverse[value] = key

    def __getitem__(self, key):
        try:
            value = dict.__getitem__(self, key)
        except KeyError:
            value = self.reverse[key]
        return value

    __getattr__ = __getitem__

def which_flags(d, flags):
    values = list(d.reverse.keys())
    values.sort()
    flag_names = []
    for v in values:
        if v & flags:
            flag_names.append(d[v])

    return '|'.join(flag_names)

# netinet6/in6_var.h
IN6_IFF = ReverseDict((
    ('IN6_IFF_ANYCAST',    _net.IN6_IFF.ANYCAST),
    ('IN6_IFF_TENTATIVE',  _net.IN6_IFF.TENTATIVE),
    ('IN6_IFF_DUPLICATED', _net.IN6_IFF.DUPLICATED),
    ('IN6_IFF_DETACHED',   _net.IN6_IFF.DETACHED),
    ('IN6_IFF_DEPRECATED', _net.IN6_IFF.DEPRECATED),
    ('IN6_IFF_NODAD',      _net.IN6_IFF.NODAD),
    ('IN6_IFF_AUTOCONF',   _net.IN6_IFF.AUTOCONF),
    ('IN6_IFF_TEMPORARY',  _net.IN6_IFF.TEMPORARY),
    ('IN6_IFF_NOPFX',      _net.IN6_IFF.NOPFX),
  )
)


# netinet6/in6.h
"""
struct sockaddr_in6 {
    uint8_t     sin6_len;   /* length of this struct */
    sa_family_t sin6_family;    /* AF_INET6 */
    in_port_t   sin6_port;  /* Transport layer port # */
    uint32_t    sin6_flowinfo;  /* IP6 flow information */
    struct in6_addr sin6_addr;  /* IP6 address */
    uint32_t    sin6_scope_id;  /* scope zone index */
};
"""
class sockaddr_in6(object):
    """A simple class for packing up a sockaddr_in6 struct."""

    format = 'BBHI%dsI' %(_net._IF_NAMESIZE)

    def __init__(self, address=None, port=0, flowinfo=0, scope_id=0):
        if address:
            self.address = socket.inet_pton(socket.AF_INET6, address)
        else:
            self.address = socket.inet_pton(socket.AF_INET6, '::')
        self.port = port
        self.flowinfo = flowinfo
        self.scope_id = 0

    def __len__(self):
        return struct.calcsize(self.format)

    def pack(self):
        return struct.pack(self.format,
            len(self),
            socket.AF_INET6,
            self.port,
            self.flowinfo,
            self.address,
            self.scope_id
        )

# net/in6_var.h
"""
struct  in6_ifreq {
    char    ifr_name[IFNAMSIZ];
    union {
        struct  sockaddr_in6 ifru_addr;
        struct  sockaddr_in6 ifru_dstaddr;
        int ifru_flags;
        int ifru_flags6;
        int ifru_metric;
        caddr_t ifru_data;
        struct in6_addrlifetime ifru_lifetime;
        struct in6_ifstat ifru_stat;
        struct icmp6_ifstat ifru_icmp6stat;
        u_int32_t ifru_scope_id[16];
    } ifr_ifru;
};
"""
class in6_ifreq(object):
    """This is a partial implementation of the in6_ifreq structure.

    This structure is basically a gigantic union. Because of this the
    constructor to this object takes the only non-union struct member and then
    there are pack_ methods for packing this struct based on the union member
    you want to use. Similarly there are unpack_ methods for unpacking the
    union member you want to use.

    unpack_ methods are static so you don't need to instantiate the class for
    no good reason.

    This class is not complete, it only offers support for the struct members
    that were needed at the time of writing. You can add more later if you
    need them.
    """

    def __init__(self, if_name):
        self.if_name = if_name

    def pack_ifru_addr(self, addr):
        """Pack an in6_ifreq selecting ifru_addr as the union member.

        :Parameters:
            -`addr`: The IPv6 address to pack

        :Return:
            A string after calling struct.pack()

        :Exceptions:
            `socket.error`: Invalid IPv6 address
        """

        format = '%ds' %(_net._IF_NAMESIZE)
        sa6 = sockaddr_in6(addr)
        return struct.pack(format, self.if_name) + sa6.pack()

    @staticmethod
    def unpack_flags6(buffer):
        """Unpack the result of an SIOCGIFAFLAG_IN6 ioctl request.

        :Parameters:
            - `buffer`: The struct returned from the ioctl call

        :Return:
            (interface name, ifru_flags6)
            ifru_flags6 is an integer, see IN6_IFF for the actual flags.
        """
        format = '%dsI' %(_net._IF_NAMESIZE)
        return struct.unpack_from(format, buffer)

def decode_flags(flags):
    """A debug routine for printing out all of the ifru_flags6 flags that
    are set."""

    print "Decoding flags:", repr(flags), repr(which_flags(IN6_IFF, flags))


def get_flags(if_name, addr):
    """Given an interface name and an IPv6 address on that interface return
    the interface flags.

    This can tell you whether or not an IPv6 address on an interface is
    tentative, deprecated, autoconfigured, etc.. See IN6_IFF's definition in
    this module for an exhaustive list of flags.

    :Parameters:
        - `if_name`: The name of the interface, ex. 'em0'
        - `addr`: The IPv6 address in presentation form that is also on
            `if_name`. ex. '2001:db8::1'

    :Return:
        flags: an integer, see the enum IN6_IFF in this module.

    :Exceptions:
        `socket.error`: You did something wrong
    """
    s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    try:
        in6_ifreq_struct = in6_ifreq(if_name).pack_ifru_addr(addr)
        # The buffer passed in is used for the result, make it 1024 bytes
        # because that's as big as python's ioctl supports.
        ia6_flags = in6_ifreq_struct + ('\0' * (1024 - len(in6_ifreq_struct)))
        result = fcntl.ioctl(s.fileno(), _net._SIOCGIFAFLAG_IN6, ia6_flags)
    finally:
        s.close()

    return in6_ifreq.unpack_flags6(result)[1]
