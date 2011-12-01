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

# $Header: //prod/main/ap/aplib/aplib/net/aplib.net._net.pyx#4 $

"""Pyrex-optimized routines for the aplib.net package.

All of these functions are exposed in other modules in the net package, you
should never need to access this module directly.
"""

__version__ = '$Revision: #4 $'

from libc cimport uint32_t
cimport libc
from stdio cimport sprintf
include "python.pxi"
include "pyrex_helpers.pyx"

cdef extern from "sys/socket.h":
    enum: AF_INET6

cdef extern from "net/if.h":
    unsigned int if_nametoindex(char *)
    enum IF_ENUM:
        IF_NAMESIZE

cdef extern from "netinet/in.h":
    pass
cdef extern from "sys/ioctl.h":
    pass

IF UNAME_SYSNAME == "FreeBSD":
    cdef extern from "net/if_var.h":
        pass

    cdef extern from "netinet6/in6_var.h":
        enum IOCTL_ENUM:
            SIOCGIFAFLAG_IN6

cdef extern from "netinet/icmp6.h":
    enum ND_ENUM:
        ND_NEIGHBOR_ADVERT
        ND_OPT_TARGET_LINKADDR
        ND_NA_FLAG_OVERRIDE

    enum IN6_IFF_ENUM:
        IN6_IFF_ANYCAST
        IN6_IFF_TENTATIVE
        IN6_IFF_DUPLICATED
        IN6_IFF_DETACHED
        IN6_IFF_DEPRECATED
        IN6_IFF_NODAD
        IN6_IFF_AUTOCONF
        IN6_IFF_TEMPORARY
        IN6_IFF_NOPFX

cdef extern from "arpa/inet.h":
    enum: INET_ADDRSTRLEN
    enum: INET6_ADDRSTRLEN

    cdef char * inet_ntop(int, void *, char *, int)
    cdef int inet_pton(int, char *, void *)

class ND:
    """For IPv6's Neighbor discovery protocol."""
    NEIGHBOR_ADVERT     = ND_NEIGHBOR_ADVERT
    OPT_TARGET_LINKADDR = ND_OPT_TARGET_LINKADDR
    NA_FLAG_OVERRIDE    = ND_NA_FLAG_OVERRIDE

IF UNAME_SYSNAME == "FreeBSD":
    class IN6_IFF:
        """Flags for IPv6 interface state."""
        ANYCAST     = IN6_IFF_ANYCAST
        TENTATIVE   = IN6_IFF_TENTATIVE
        DUPLICATED  = IN6_IFF_DUPLICATED
        DETACHED    = IN6_IFF_DETACHED
        DEPRECATED  = IN6_IFF_DEPRECATED
        NODAD       = IN6_IFF_NODAD
        AUTOCONF    = IN6_IFF_AUTOCONF
        TEMPORARY   = IN6_IFF_TEMPORARY
        NOPFX       = IN6_IFF_NOPFX

IF UNAME_SYSNAME == "FreeBSD":
    # Request flags for IPv6 address
    _SIOCGIFAFLAG_IN6 = SIOCGIFAFLAG_IN6

# Buffer size for an interface name
_IF_NAMESIZE = IF_NAMESIZE

cdef int _scan_octet(char *str, unsigned int *result, char **stop_ptr):
    """Parse an IP octect in decimal.

    Parsing stops at the first non-digit character.

    This will fail if no digit is found or if the value is greater than 255.

    :Parameters:
        - `str`: The number to parse.
        - `result`: The result is stored here.
        - `stop_ptr`: The pointer to the character that stopped the parsing is
          stored here.

    :Return:
        Returns 0 on success, -1 on error.
    """
    cdef unsigned int ch
    cdef unsigned int value
    cdef char *ptr

    ptr = str
    value = 0
    while 1:
        ch = <unsigned int> <unsigned char> (ptr[0] - c'0')
        if ch >= 10:
            break
        value = value * 10 + ch
        if value > 255:
            return -1
        ptr = ptr + 1

    if ptr == str:
        # Never saw a digit.
        return -1

    result[0] = value
    stop_ptr[0] = ptr
    return 0

cdef char *lower_hex_nums
lower_hex_nums = "0123456789abcdef"

cdef libc.size_t fmt_hex(unsigned int value, char *str):
    """Convert a number to a string in hex.

    The hex string is NOT null terminated.  The hex digits are in lower case.

    :Parameters:
        - `value`: The value to convert.
        - `str`: Where to store the string.

    :Return:
        Returns the length of the hex string.
    """
    cdef libc.size_t len
    cdef int q

    len = 1
    q = value
    while q > 15:
        len = len + 1
        q = q / 16
    str = str + len
    while 1:
        str = str - 1
        str[0] = lower_hex_nums[value % 16]
        value = value / 16
        if not value:
            break
    return len

cdef int _parse_ipv4(char *address, uint32_t *result, char **stop_ptr):
    """Parse an IPv4 address.

    :Parameters:
        - `address`: The IP address to parse.
        - `result`: Output of the result.
        - `stop_ptr`: The character that caused parsing to stop is stored here.

    :Return:
        Returns 0 on success, -1 on error.
    """
    cdef unsigned int octet
    cdef uint32_t value

    value = 0

    if _scan_octet(address, &octet, &address) == -1:
        return -1
    if address[0] != c'.':
        return -1
    address = address + 1
    value = octet << 24

    if _scan_octet(address, &octet, &address) == -1:
        return -1
    if address[0] != c'.':
        return -1
    address = address + 1
    value = value | octet << 16

    if _scan_octet(address, &octet, &address) == -1:
        return -1
    if address[0] != c'.':
        return -1
    address = address + 1
    value = value | octet << 8

    if _scan_octet(address, &octet, &address) == -1:
        return -1
    value = value | octet

    result[0] = value
    stop_ptr[0] = address
    return 0

cdef int _isalnum(int ch):
    return ((ch >= c'0' and ch <= c'9') or
            (ch >= c'a' and ch <= c'f') or
            (ch >= c'A' and ch <= c'F'))

##############################################################################

def parse_ipv4(address):
    """Parse an IPv4 address.

    The value is returned in host byte-order.  Use the ``struct`` module to
    convert to a string of bytes in the appropriate byte order if necessary.

    This does NOT support short-form addresses (such as 127.1 or class networks
    with less than 4 octets).

    :Parameters:
        - `address`: The IP address to parse.

    :Return:
        Returns the IP address as an integer or None in case of error.

    """
    cdef char *stop
    cdef uint32_t result

    if _parse_ipv4(address, &result, &stop) == -1:
        return None
    if stop[0] != c'\0':
        return None
    return minimal_ulong(result)

def parse_cidr4(address):
    """Parse an IPv4 address with an optional CIDR prefix.

    See `parse_ipv4` for more detail.

    If no prefix is given, then a value of 32 is returned.

    :Parameters:
        - `address`: The IP address to parse.

    :Return:
        Returns a tuple ``(ip_int, prefixlen)`` where ``ip_int`` is the integer
        of the IP and ``prefixlen`` is the integer value of the network prefix.
        In case of error, returns None.

    """
    cdef char *stop
    cdef uint32_t result
    cdef unsigned int prefix

    if _parse_ipv4(address, &result, &stop) == -1:
        return None
    if stop[0] == c'\0':
        prefix = 32
    elif stop[0] == c'/':
        if _scan_octet(stop+1, &prefix, &stop) == -1:
            return None
        if stop[0] != c'\0':
            return None
        if prefix > 32:
            return None
    else:
        return None

    return (minimal_ulong(result), prefix)

def parse_ipv6(address):
    """Parse an IPv6 address.

    The value is returned in network byte-order.  Use the ``struct`` module to
    convert to a string of bytes in the appropriate byte order if necessary.

    :Parameters:
        - `address`: The IP address to parse.

    :Return:
        Returns the IP address as a python string which represents packed ip,
        or None in case IP is invalid.
    """

    cdef char result[16]
    if not inet_pton(AF_INET6, address, result):
        return None
    return PyString_FromStringAndSize(result, 16)

def parse_ipv6_prefix(address):
    """Parse an IPv6 address with an optional network prefix.

    See `parse_ipv6` for more detail.

    If no prefix is given, then a value of 128 is returned.

    :Parameters:
        - `address`: The IP address to parse.

    :Return:
        Returns a tuple ``(ip, prefixlen)`` where ``ip`` is the packed ip as
        a string and ``prefixlen`` is the integer value of the network prefix,
        or None in case IP is invalid.
    """

    # A more simpler way to do this would be to use inet_cidr_pton, but that
    # treats numbers (123456) as valid IP strings. Though that is correct, the
    # existing API explicitly prevents it. Hence the following logic.
    cdef int prefix
    cdef unsigned int tmp
    cdef char res[16]
    cdef char *ptr = address
    cdef int ind = address.rfind('/')
    prefix = 128
    if ind != -1:
        if _scan_octet(ptr+ind+1, &tmp, &ptr) == -1:
            return None
        if tmp > 128:
            return None
        prefix = tmp
        address = address[:ind]
    if not inet_pton(AF_INET6, address, res):
        return None
    return (PyString_FromStringAndSize(res, 16), prefix)

def ipv4_htop(packed_ip):
    """Convert a packed IPv4 address in host-byte order to string.

    :Parameters:
        - `packed_ip`: The IP address to convert.

    :Return:
        Returns the string representation of the IP.
    """

    cdef char res[INET_ADDRSTRLEN]
    cdef unsigned int ip = packed_ip
    sprintf(res, "%d.%d.%d.%d", ip>>24, ip>>16 & 0xff, ip>>8 & 0xff, ip & 0xff)
    return res

def ipv6_ntop(ip):
    """Convert a packed IPv6 address to string.

    :Parameters:
        - `ip`: The IP address to convert.

    :Return:
        Returns the string representation of the IP.
    """

    cdef char res[INET6_ADDRSTRLEN]
    inet_ntop(AF_INET6, <char *>ip, res, INET6_ADDRSTRLEN)
    return res

def if_name_to_index(if_name):
    """Get the interface index number for the named interface.

    :Parameters:
        - `if_name`: The name of the interface, ex. em0

    :Return:
        Returns the interface index as an integer.

    :Exceptions:
        - `aplib.oserrors.ENXIO`: The interface name couldn't be found.
           See if_nametoindex(3) for other exceptions that might be raised.
    """

    idx = if_nametoindex(if_name)
    if idx == 0:
        raise_oserror()

    return idx

