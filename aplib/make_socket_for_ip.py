import aplib.net.ip as net_ip
import coro
import socket

def make_socket_for_ip(ip, stype=socket.SOCK_STREAM):
    """Create a socket object with the correct address family for ip.

    :Parameters:
        - `ip`: An IP address as a string
        - `stype`: The socket type (see `SOCK`).

    :Return:
        Returns a socket object.

    :Exceptions:
        - `OSError`: OS-level error.
        - `ValueError`: Invalid IP address.
    """

    if net_ip.is_ipv4(ip):
        return coro.make_socket(socket.AF_INET, stype)
    elif net_ip.is_ipv6(ip):
        return coro.make_socket(socket.AF_INET6, stype)
    else:
        raise ValueError('Invalid IP address')
