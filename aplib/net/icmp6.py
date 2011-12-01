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

import ifmedia
import socket
import struct

from aplib.net.interface import name_to_index
from aplib.net import _net

"""Code for sending out ICMPv6 packets.

Today this code is used for generating unsolicited neighbor announcement
(NA) messages. These are used to expeditiously update network
infrastructure of a change in a MAC address. This can happen in our
product if someone is using NIC failover and we actually do the
failover. If we do nothing network switches will eventually figure out
that the MAC address and physical port for a given IP changed. However,
if we send out this unsolicited NA we can immediately notify our
neighbors that things have changed.

This code is difficult to test. The best way I found to test it was to
setup another FreeBSD host next to the one we're running this code on.

On the neighboring FreeBSD host run `ndp -a`. This will print out the
neighbor cache. You should find the IP of this host and it's MAC
address.

Down in the __main__ section you can plugin that IP address and a new
MAC address. The IP address needs to stay the same, FreeBSD hosts will
only update the cache for an IP it already has cached. Change the MAC
address variable and then run this script, as root (SOCK_RAW). Run `ndp
-a` on the neighboring host again and verify that the MAC address
changed. If it didn't, something is wrong.

On the neighboring host run `netstat -s -p icmp6` and look toward the
bottom for 'bad neighbor advertisement message'. If that value is > 0
verify that you're the one doing it. Run this script again, did the
value increment? If it did, you're sending bogus NAs.

The first check you should do is with tcpdump. Do a capture of this
packet and load it up in wireshark to verify that the data on the wire
is the same data you think you're sending. If everything pans out then
you'll need to enable debugging for the neighbor discovery protocol.
This is done in sys/netinet6/nd6.c. I just delete the #ifdef statements
and set nd6_debug = 1. Now recompile the kernel and update the
neighboring host.  Once that is installed you can rerun your tests,
error messages will go to /var/log/messages, grep for nd6.

"""

class ICMP6Header(object):
    """
    u_int8_t    icmp6_type; /* type field */
    u_int8_t    icmp6_code; /* code field */
    u_int16_t   icmp6_cksum;    /* checksum field */
    union {
        u_int32_t   icmp6_un_data32[1]; /* type-specific field */
        u_int16_t   icmp6_un_data16[2]; /* type-specific field */
        u_int8_t    icmp6_un_data8[4];  /* type-specific field */
    } icmp6_dataun;
    """

    def __init__(self, icmp_type, icmp_code, data):
        self.icmp_type = icmp_type
        self.icmp_code = icmp_code
        self.data = data

    def pack(self):
        return struct.pack('>BBHI',
            self.icmp_type, self.icmp_code, 0, self.data)

class IN6Addr(object):
    """
    union {
        uint8_t     __u6_addr8[16];
        uint16_t    __u6_addr16[8];
        uint32_t    __u6_addr32[4];
    } __u6_addr;            /* 128-bit IP6 address */
    """
    def __init__(self, ip):
        """Takes an IPv6 address as a string."""
        self.ip_as_bytes = socket.inet_pton(socket.AF_INET6, ip)

    def pack(self):
        return self.ip_as_bytes

class NDOptLinkLayer(object):
    """
    u_int8_t    nd_opt_type;
    u_int8_t    nd_opt_len;
    /* followed by option specific data*/
    """
    def __init__(self, mac_address):
        """mac_address as a string (00:13:72:66:e2:43)

        Things get a bit tricky here. This will only ever work with 48-bit mac
        addresses.
        """
        self.mac_address = mac_address

        # 2 bytes for the two struct fields
        # 6 bytes for the 48-bit mac address
        self.opt_len = 2 + 6
        # round up to 8 byte alignment, copied from FreeBSD's nd6_na_output
        self.opt_len = (self.opt_len + 7) & ~7
        self.opt_len >>= 3

        self.opt_type = _net.ND.OPT_TARGET_LINKADDR

    def pack(self):
        mac_parts = self.mac_address.split(':')
        for i in range(len(mac_parts)):
            mac_parts[i] = int(mac_parts[i], 16)
        return struct.pack('>BB6B', self.opt_type, self.opt_len, *mac_parts)

class NDNeighborAdvert(object):
    """
    struct icmp6_hdr    nd_na_hdr;
    struct in6_addr     nd_na_target;   /* target address */
    """

    def __init__(self, ip, mac_address):
        """ip and mac_address are the ip and mac addresses of -this- host."""

        self.ip = ip
        self.mac_address = mac_address

    def pack(self):
        icmp6_header = ICMP6Header(
            _net.ND.NEIGHBOR_ADVERT, 0, _net.ND.NA_FLAG_OVERRIDE).pack()
        nd_na_target = IN6Addr(self.ip).pack()
        nd_opt = NDOptLinkLayer(self.mac_address).pack()

        return icmp6_header + nd_na_target + nd_opt


def send_na(ip, mac, if_name):
    # Do we need the mac given that we have if_name?
    # ifmedia.ethernet_mac('em0') -> '00:13:72:66:e2:42'
    # maybe an optional arg so that it can be overridden (spoofed?)

    icmp_packet = NDNeighborAdvert(ip, mac).pack()

    s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6)

    # The hoplimit must be 255 so that the receiver can verify that the
    # packet has not been forwarded. RFC 3542 sec 6.3
    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 255)

    # Set the interface to use for multicast with this socket
    if_idx = name_to_index(if_name)
    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, if_idx)

    # Tell the OS not to loop this packet back to ourselves.
    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 0)

    s.sendto(icmp_packet, ('ff02::1', 0))

if __name__ == '__main__':
    import subprocess
    import time
    from aplib.net.interface import get_flags, decode_flags

    new_ip = '2001:db8:59ff::1'
    if_name = 'em0'
    mac = '00:13:72:66:e2:42'

    cfg_cmd = 'ifconfig %s inet6 %s prefixlen 64' %(if_name, new_ip)
    delete_cmd = cfg_cmd + ' delete'
    subprocess.Popen(delete_cmd.split())
    subprocess.Popen(cfg_cmd.split())
    cmd = 'ifconfig %s' %(if_name,)
    ifconfig = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    print ifconfig.stdout.read()

    send_na(new_ip, mac, if_name)

    # Show the flags set on an interface immediately after configuring it
    for i in range(11):
        time.sleep(.1)
        try:
            if_flags = get_flags(if_name, new_ip)
            decode_flags(if_flags)
        except socket.error, e:
            print "try", i
            print "socket.error:", e


