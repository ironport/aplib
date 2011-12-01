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

# $Header: //prod/main/ap/aplib/aplib/net/ip.py#9 $

"""IP address object.

Introduction
============
This module provides an encapsulation around an IP address and network prefix.
There is a base `BaseIP` class with two subclasses: `IPv4` and `IPv6`.  There
is a wrapper function called `IP` for creating either a v4 or v6 object.  If
you want to enforce either v4 or v6 addresses in your code, then instantiate
the IPv4 or IPv6 classes directly.

An IP object encompases the IP address and the network prefix (aka "netmask" or
CIDR). There is a separate module `aplib.net.mask` for objects that represent a
mask, and a module `aplib.net.range` for representing an entire network (or
range of IP addresses).

IP addresses, Mask objects, and Range objects are all intended to be immutable
objects.

Usage
=====
It may be easiest to describe how to use the IP object by example.

The basic operation of creating an IP object::

    >>> IP('1.2.3.4')
    IPv4('1.2.3.4')
    >>> IP('2001:db8::1')
    IPv6('2001:db8::1')

Normalize an IP and return it as a string::

    >>> str(IP('001.002.003.004'))
    '1.2.3.4'

The above has an implicit prefix of 32 for IPv4 or 128 for IPv6.
You can create an IP with an explicit network prefix::

    >>> IP('1.2.3.4/24')
    IPv4('1.2.3.4/24')
    >>> IP('2001:db8::1/32')
    IPv6('2001:db8::1/32')

IP range objects interoperate with IP objects::

    >>> x = IP('1.2.3.4/24')
    >>> n = x.network
    >>> n
    Prefix('1.2.3.0/24')
    >>> x in n
    True

Get IP information in integer form::

    >>> x = IP('1.2.3.4/24')
    >>> int(x)
    16909060
    >>> x.ip
    16909060
    >>> hex(_)
    '0x1020304'
    >>> hex(x)
    '0x01020304'
    >>> x.prefixlen
    24
    >>> hex(x.netmask_int)
    '0xffffff00L'
    >>> hex(int(x.hostmask))
    '0xffL'

Generally you should try to avoid using the integer forms.  Things like the
Mask and IPRange objects provide abstractions that should obviate the need for
dealing with low-level values.  Whenever dealing with integers, this library
uses host-byte order.  If you need to represent a value in bytes of a specific
byte order, use the struct module to convert to the format that you want.

A method to guess the gateway address for an IPv4 object::

    >>> x = IP('1.2.3.4/24')
    >>> x.network[0] + 1
    IPv4('1.2.3.1')

Use classic-style netmasks (only applicable to IPv4):

    >>> IPv4('1.2.3.4', netmask='0xffffff00')
    IPv4('1.2.3.4/24')
    >>> IPv4('1.2.3.4', netmask='255.255.255.0')
    IPv4('1.2.3.4/24')

There are many other things you can do with an IP object.  Browse the API for
other functions and features.

Future
======
- Add IPv6 scope information (like fe80::3%eth0), aka "zone index".

- Option to format IPv6 without compression (no ::).  Also, maybe without
  removing leading zeros for a fixed-width output.

- Add a supernet method to get the next higher network (opposite of subnet).
  The distinction of supernet/subnet methods as they interact with the IP
  and IPRange objects should be clarified.
"""

__version__ = '$Revision: #9 $'

from aplib.net import _net
from aplib.net.mask import Mask4, Mask6
from aplib.net.exceptions import *
from aplib.net.range import Prefix
import struct

cidr_fn = {4 : _net.parse_cidr4, 6: _net.parse_ipv6_prefix}

def IP(address, netmask=None):
    """Create an IP address object.

    This creates an IP address of either IPv4 or IPv6 based on the syntax.

    Beware that integer values can be ambiguous.  Values less than or equal to
    (2**32-1) are interpreted as IPv4 values.  Thus the integer "1" returns
    IPv4('0.0.0.1'), not IPv6('::1').

    The address may end with optional prefix notation such as '1.2.3.4/24'. See
    the `IPv4` and `IPv6` object docstrings for detail on the specific syntax
    supported for those objects.

    :Parameters:
        - `address`: The address.  This can be either an integer or string.
        - `netmask`: An optional netmask to apply to this IP.

    :Return:
        Returns either an `IPv4` or `IPv6` instance.

    :Exceptions:
        - `IPValidationError`: The format of the IP is not valid.
    """
    try:
        return IPv4(address, netmask)
    except Error:
        pass

    try:
        return IPv6(address, netmask)
    except Error:
        pass

    raise IPValidationError(address)

def is_ip(address):
    """Determine if an address is an IP address.

    :Parameters:
        - `address`: The IP address string to check.

    :Return:
        Returns True if it is either a v4 or v6 address, otherwise False.
    """
    return is_ipv4(address) or is_ipv6(address)

def is_ipv4(address):
    """Determine if an address is an IPv4 address.

    :Parameters:
        - `address`: The IP address string to check.

    :Return:
        Returns True if it is a v4 address, otherwise False.
    """
    return _net.parse_ipv4(address) is not None

def is_ipv6(address):
    """Determine if an address is an IPv6 address.

    :Parameters:
        - `address`: The IP address string to check.

    :Return:
        Returns True if it is a v6 address, otherwise False.
    """
    return _net.parse_ipv6(address) is not None

def is_cidr(address, version=None, accept_ip=True):
    """Determine if an address is a Valid CIDR.

    :Parameters:
        - `address`: The IP address string to check.
        - `version`: The IP address version to check - 4 : IPv4, 6 : IPv6, None : both.
        - `accept_ip`: If true, treat IP addresses also as valid.

    :Return:
        Returns True if it is a cidr, otherwise False.

    """
    if version is None:
        return is_cidr(address, 4, accept_ip) or is_cidr(address, 6, accept_ip)
    valid_cidr = cidr_fn[version](address) is not None
    if not accept_ip:
        return valid_cidr and '/' in address
    return valid_cidr

def htop(value):
    """Converts from packed address in host-byte order to presentation format or
    ip address string.

    :Parameters:
        - `value`: the packed ip to convert.

    :Return:
        Returns the ip address string (v4 or v6).

    :Exceptions:
        - `IPValidationError`: if the given value is out of scope for v6.
    """
    if value >= 0 and value <= IPv4.FULL_MASK:
        return IPv4.int_to_str(value)
    return IPv6.int_to_str(value)

def ptoh(address):
    """Converts from presentation format or ip address string to packed address
    in host-byte order.

    :Parameters:
        - `address`: The IP address string to convert.

    :Return:
        Returns the packed ip address.

    :Exceptions:
        - `IPValidationError`: if address is not valid v4 or v6 address.
    """

    result = _net.parse_ipv4(address)
    if result is None:
        return IPv6.parse_ip(address)
    return result

class BaseIP(object):

    """Base IP class.

    This implements the shared logic between the `IPv4` and `IPv6` objects. You
    cannot instantiate it directly.

    This object is intended to be immutable.  It implements the hash method, so
    you can use it as a value in a dictionary.  It also supports comparison
    with other IP objects, so it can be sorted in a list.

    In some cases you can use this object interchangeably with integers.
    For example:

    - ``int(obj)`` returns the integer value of the IP.
    - ``hash(obj)`` returns a hash of the object.
    - ``obj + 1`` will return an IP address object with the IP value increased
      by one.

    :IVariables:
        - `ip`: The IP address as an integer in host-byte order.
        - `prefixlen`: The prefix length of the network.
        - `version`: The address version, either 4 or 6.
        - `localhost`: An IP object that represents localhost.
        - `WIDTH`: The number of bits in this address type, either 32 or 128.
        - `FULL_MASK`: An integer of the full bitmask for this address type.
        - `_mask`: The Mask class that matches this address type (Mask4 or
          Mask6).
        - `_netmask`: The netmask as an integer (stored for performance).
    """

    __slots__ = ('ip', 'prefixlen', '_netmask')

    version = None
    WIDTH = None
    FULL_MASK = None
    _mask = None
    localhost = None

    def __init__(self, address, netmask=None):
        """Initialize an IP object.

        :Parameters:
            - `address`: The IP address.  May be an integer or a string. See
              the appropriate subclass docstring for the exact syntax
              supported.
            - `netmask`: The netmask to use.  This may either be a
              `aplib.net.mask.Mask` instance or a string or an integer.
              See the Mask docstring for details on formats supported.
              It is an error to specify a netmask when the address
              includes a prefix length.

        :Exceptions:
            - `IPValidationError`: Invalid address.
            - `MaskValidationError`: The netmask is invalid.
        """

        if isinstance(address, (int, long)):
            if address < 0 or address > self.FULL_MASK:
                raise IPValidationError(address)
            self.ip = address
            if netmask is None:
                self.prefixlen = self.WIDTH
                self._netmask = self.FULL_MASK
            else:
                self._set_netmask(netmask)
        else:
            self.ip, self.prefixlen = self.parse_ip_prefix(address)
            if netmask is None:
                self._netmask = self._mask.prefixlen_to_mask(self.prefixlen)
            else:
                if self.prefixlen == self.WIDTH:
                    self._set_netmask(netmask)
                else:
                    # Can't have both a prefix address and a netmask.
                    raise MaskValidationError(netmask)

    def _set_netmask(self, netmask):
        if isinstance(netmask, self._mask):
            if not netmask.is_netmask():
                raise MaskValidationError(netmask)
            self._netmask = netmask.mask
            self.prefixlen = netmask.prefixlen
        elif isinstance(netmask, basestring):
            self.prefixlen, self._netmask, format = self._mask.parse_mask(netmask)
        elif isinstance(netmask, (int, long)):
            if netmask < 0 or netmask > self.FULL_MASK:
                raise MaskValidationError(netmask)
            self._netmask = netmask
            # This will take care of validation.
            self.prefixlen = self._mask.mask_to_prefixlen(netmask)
        else:
            raise MaskValidationError(netmask)

    @staticmethod
    def parse_ip_prefix(address):
        """Parse an IP address with an optional network prefix.

        See the subclass class docstring for details on the format supported.

        :Parameters:
            - `address`: The address to parse.

        :Return:
            Returns a ``(ip_int, prefixlen)`` tuple.

        :Exceptions:
            - `IPValidationError`: The address is not valid.
        """
        raise NotImplementedError

    @staticmethod
    def parse_ip(address):
        """Parse an IP address.

        This does NOT allow a network prefix.

        See the subclass class docstring for details on the format supported.

        :Parameters:
            - `address`: The address to parse.

        :Return:
            Returns an integer of the IP.

        :Exceptions:
            - `IPValidationError`: The address is not valid.
        """
        raise NotImplementedError

    @classmethod
    def int_to_str(cls, value):
        """Convert an integer to an IP string.

        :Parameters:
            - `value`: The integer to convert.

        :Return:
            Returns a string of the IP address.

        :Exceptions:
            - `IPValidationError`: The value is out of range for this IP type.
        """
        raise NotImplementedError

    def is_private(self):
        """Determine if this is a "private" address.

        Private addresses are those defined in RFC 1918 for IPv4 or the Unique
        Local Address (ULA) in IPv6.

        :Return:
            Returns a boolean of whether or not this is a "private" address.
        """
        raise NotImplementedError

    def is_multicast(self):
        """Determine if this is a multicast address.

        :Return:
            Returns a boolean of whether or not this is a multicast address.
        """
        raise NotImplementedError

    def is_loopback(self):
        """Determine if this is a loopback address.

        :Return:
            Returns a boolean of whether or not this is a loopback address.
        """
        raise NotImplementedError

    def is_link_local(self):
        """Determine if this is a link-local address.

        See RFC 3927 for IPv4 and RFC 4291 for IPv6.

        :Return:
            Returns a boolean of whether or not this is a link-local address.
        """
        raise NotImplementedError

    def is_unspecified(self):
        """Determine if this is the "unspecified" address.

        The unspecified address is 0.0.0.0 for IPv4 and :: for IPv6.

        :Return:
            Returns a boolean of whether or not this is the unspecified
            address.
        """
        return self.ip == 0

    def reverse_dns_pieces(self, to_append=''):
        """Convert the IP into a string that looks a lot like a PTR lookup.

        This reverses the IP address and converts it to a string appropriate
        for DNS Blacklist queries. This is basically the same as reverse_dns()
        but without the .ip6.arpa or .in-addr.arpa suffix.

        For example::

            IP('1.2.3.4').reverse_dns_pieces() -> '4.3.2.1'
            IP('1.2.3.4').reverse_dns_pieces('suffix') -> '4.3.2.1.suffix'

        :Parameters:
            - `to_append`: A string to append to the end of the reversed IP

        :Return:
            Returns a string of the reversed IP.
        """
        raise NotImplementedError

    def reverse_dns(self):
        """Convert the IP into a string suitable for a PTR lookup in DNS.

        This reverses the IP address and converts it to a string appropriate
        for PTR lookups in DNS.  For IPv6 it uses ip6.arpa, not the obsoleted
        ip6.int format.

        :Return:
            Returns a string of the IP address for a PTR lookup.
        """
        raise NotImplementedError

    @property
    def forward_dns_rr_type(self):
        """Return the DNS RR type to use for for this version of IP.

        :Return:
            The string 'AAAA' for IPv6 or 'A' for IPv4.
        """
        raise NotImplementedError

    def format(self, always_prefix=False):
        """Format the IP to a string.

        :Parameters:
            - `always_prefix`: If True, will always include the network prefix.
              If False (the default) then it will exclude the network prefix if
              it is the full width (only 1 IP).

        :Return:
            Returns a string representation of the IP and network.
        """
        if not always_prefix and self.prefixlen == self.WIDTH:
            return self.int_to_str(self.ip)
        else:
            return '%s/%i' % (self.int_to_str(self.ip),
                              self.prefixlen)

    @property
    def network(self):
        """The network for this IP.

        The value is an `aplib.net.range.Prefix` instance that represents the
        network for this IP.
        """
        return Prefix(self)

    @property
    def netmask(self):
        """The netmask for this IP.

        The value is an `aplib.net.mask.Mask` instance that represents the
        netmask for this IP.
        """
        return self._mask(self._netmask)

    @property
    def netmask_int(self):
        """The netmask as an integer.

        The value is an integer representing the netmask for this IP.
        """
        return self._netmask

    @property
    def hostmask(self):
        """The hostmask for this IP.

        The value is an `aplib.net.mask.Mask` instance that represents the
        hostmask for this IP.
        """
        return self._mask(self._netmask ^ self.FULL_MASK)

    @property
    def broadcast(self):
        """The broadcast address for this IP.

        IPv6 doesn't really have a concept of a "broadcast address". However,
        it is sometimes convenient to get the last IP address in a network
        range, and the terminology is in common use to represent the last IP,
        so for IPv6 it just returns the last IP in the network.

        The value is a `BaseIP` instance that represents the "broadcast"
        address for this IP.
        """
        return self.__class__(self.ip | (self._netmask ^ self.FULL_MASK))

    def subnet(self, prefixlen_diff=1):
        """Return a list of subnets of this IP network.

        The prefix is modified by the given value.  So, for example, an address
        of '1.2.3.4/24' with a diff of ``1`` will return a list of 2 IP's:
        ``IPv4('1.2.3.0/25')`` and ``IPv4(1.2.3.128/25')``. The number of
        results is equal to ``2**prefixlen_diff``.  A standalone IP (/32 for
        IPv4) will return a list of one element with that IP.

        :Parameters:
            - `prefixlen_diff`: The amount to modify the prefix address by.
              Values greater than the width of this address type will be
              clamped to the max width.

        :Return:
            Returns a list of IP address objects.
        """
        new_prefix = self.prefixlen + prefixlen_diff
        if new_prefix > self.WIDTH:
            new_prefix = self.WIDTH
        new_mask = self._mask.prefixlen_to_mask(new_prefix)
        first = self.__class__(self.ip & new_mask, netmask=new_mask)
        result = [first]
        current = first
        while 1:
            broadcast = current.broadcast
            if broadcast == self.broadcast:
                break
            current = self.__class__(int(broadcast)+1, netmask=new_mask)
            result.append(current)
        return result

    def __str__(self):
        return self.format()

    def __repr__(self):
        return '%s(\'%s\')' % (self.__class__.__name__,
                               self.format())

    def __int__(self):
        return self.ip

    def __long__(self):
        return self.ip

    def __hash__(self):
        return hash((self.version, self.ip, self.prefixlen))

    def __hex__(self):
        return '0x%0*x' % (self.WIDTH/4, self.ip)

    def __add__(self, other):
        return self.__class__(self.ip + int(other))

    def __sub__(self, other):
        return self.__class__(self.ip - int(other))

    def __eq__(self, other):
        try:
            return (self.version == other.version and
                    self.ip == other.ip and
                    self.prefixlen == other.prefixlen)
        except AttributeError:
            return NotImplemented

    def __ne__(self, other):
        try:
            return (self.version != other.version or
                    self.ip != other.ip or
                    self.prefixlen != other.prefixlen)
        except AttributeError:
            return NotImplemented

    def __lt__(self, other):
        try:
            return ((self.version, self.ip, self.prefixlen) <
                    (other.version, other.ip, other.prefixlen))
        except AttributeError:
            return NotImplemented

    def __le__(self, other):
        try:
            return ((self.version, self.ip, self.prefixlen) <=
                    (other.version, other.ip, other.prefixlen))
        except AttributeError:
            return NotImplemented

    def __gt__(self, other):
        try:
            return ((self.version, self.ip, self.prefixlen) >
                    (other.version, other.ip, other.prefixlen))
        except AttributeError:
            return NotImplemented

    def __ge__(self, other):
        try:
            return ((self.version, self.ip, self.prefixlen) >=
                    (other.version, other.ip, other.prefixlen))
        except AttributeError:
            return NotImplemented

    def __getstate__(self):
        return (self.ip, self.prefixlen, self._netmask)

    def __setstate__(self, data):
        self.ip, self.prefixlen, self._netmask = data

class IPv4(BaseIP):

    """IPv4 object.

    The IPv4 object only supports the address syntax of a dotted quad (it does
    not support addresses like ``127.1``).  The address may end with optional
    prefix notation such as '1.2.3.4/24', which can be a value from 0 to 32.

    See `BaseIP` docstring for more detail.
    """

    __slots__ = ()

    version = 4
    _mask = Mask4
    WIDTH = Mask4.WIDTH
    FULL_MASK = Mask4.FULL_MASK

    @staticmethod
    def parse_ip_prefix(address):
        ip = _net.parse_cidr4(address)
        if ip is None:
            raise IPValidationError(address)
        return ip

    @staticmethod
    def parse_ip(address):
        ip = _net.parse_ipv4(address)
        if ip is None:
            raise IPValidationError(address)
        return ip

    @classmethod
    def int_to_str(cls, value):
        if value < 0 or value > cls.FULL_MASK:
            raise IPValidationError(value)
        return _net.ipv4_htop(value)

    def is_private(self):
        return (self in Prefix('10.0.0.0/8') or
                self in Prefix('172.16.0.0/12') or
                self in Prefix('192.168.0.0/16')
               )

    def is_multicast(self):
        return self in Prefix('224.0.0.0/4')

    def is_loopback(self):
        return self in Prefix('127.0.0.0/8')

    def is_link_local(self):
        return self in Prefix('169.254.0.0/16')

    def reverse_dns_pieces(self, to_append=''):
        if to_append:
            to_append = '.' + to_append
        value = self.ip
        return '%d.%d.%d.%d%s' % (value & 0xff,
                                  value>>8 & 0xff,
                                  value>>16 & 0xff,
                                  value>>24,
                                  to_append)

    def reverse_dns(self):
        return self.reverse_dns_pieces('in-addr.arpa')

    @property
    def forward_dns_rr_type(self):
        return 'A'

IPv4.localhost = IPv4('127.0.0.1')


class IPv6(BaseIP):

    """IPv6 object.

    The IPv6 object supports standard IPv6 syntax (either lower or upper case
    hex digits), along with the optional compressed form.  See RFC 4291 for
    more detail.  The address may end with optional prefix notation such as
    '2001:db8::/32', which can be a value from 0 to 128.

    This also supports the v4 mapped syntax, such as "::13.1.68.3" or
    "::ffff:129.144.52.38". Note that the first style is known as
    "IPv4-Compatible IPv6 address" and is deprecated and should not be used.
    The second style is known as "IPv4-Mapped IPv6 address".
    """

    __slots__ = ()

    version = 6
    _mask = Mask6
    WIDTH = Mask6.WIDTH
    FULL_MASK = Mask6.FULL_MASK

    @staticmethod
    def parse_ip_prefix(address):
        ip_prefix = _net.parse_ipv6_prefix(address)
        if ip_prefix is None:
            raise IPValidationError(address)
        return (_unpack(ip_prefix[0]), ip_prefix[1])

    @staticmethod
    def parse_ip(address):
        ip = _net.parse_ipv6(address)
        if ip is None:
            raise IPValidationError(address)
        return _unpack(ip)

    @classmethod
    def int_to_str(cls, value):
        if value < 0 or value > cls.FULL_MASK:
            raise IPValidationError(value)
        return _net.ipv6_ntop(struct.pack('!2Q', value >> 64,
                                                 value & 0xffffffffffffffff))

    def is_private(self):
        return self in Prefix('fc00::/7')

    def is_multicast(self):
        return self in Prefix('ff00::/8')

    def is_loopback(self):
        return self.ip == 1 and self.prefixlen == 128

    def is_link_local(self):
        return self in Prefix('fe80::/10')

    def reverse_dns_pieces(self, to_append=''):
        result = [None]*32
        if to_append:
            result.append(to_append)
        value = self.ip
        for index in xrange(32):
            result[index] = '%x' % (value & 0xf,)
            value >>= 4

        return '.'.join(result)

    def reverse_dns(self):
        return self.reverse_dns_pieces('ip6.arpa')

    @property
    def forward_dns_rr_type(self):
        return 'AAAA'

def _unpack(address):
    i, j = struct.unpack('!2Q', address)
    return i << 64 | j

IPv6.localhost = IPv6('::1')
