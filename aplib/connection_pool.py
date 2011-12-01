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

import aplib.net.ip as ip
import time

"""
ConnectionManager manages ConnectionPools.

A ConnectionPool is associated with a particular host,port combo

A ConnectionPool contains 1 or more connections, zero of which are guaranteed
to be in a free and connected state.

A connection maintains a socket that is connected to an end point. If the
connection times out either locally or on the remote end the socket is closed.

The ConnectionPool periodically checks the state of its Connections and destroys any inactive Connection objects.

The ConnectionManager periodically checks the state of its ConnectionPools and removes reference to any that have zero Connections left.

A ConnectionManager has limits on the maximum number of ConnectionPools it will create.

Exceeding any of these limits results in an exception being raised and the
connection is not created. This behavior is preferred over creating a queue for
two reasons: This is simpler and the queue only introduces latency.

"""

# How long to not use a socket before we decide to close it
sock_timeout = 40

class MaxConnectionsLimit(Exception):

    """Max connections limit exceeded for a connection
    pool."""

    def __init__(self, host, port):
        self.host = host
        self.port = port

class IfaceNotCompatible(Exception):

    """IP family of the interface to bind to and remote host do not match."""

    def __init__(self, host, port):
        self.host = host
        self.port = port

class Connection(object):
    __slots__ = ('host', 'port', 'bind_address', 'last_used_time', 'in_use',
                 'sock')
    def __init__(self, host, port, bind_address):
        self.host = host
        self.port = port
        self.bind_address = bind_address
        self.last_used_time = time.time()
        self.in_use = False
        self.sock = None

        self.init_socket()

    def init_socket(self):
        """Initialize socket.  This method MUST be implemented by child
        classes."""
        raise NotImplementedError

    def close(self):
        """Close this connection."""
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def is_usable(self):
        """
        Return True if the connection is still usable.
        False otherwise.
        """
        if self.sock is not None:
            conn_old = time.time() - self.last_used_time > sock_timeout
            if self.in_use or not conn_old:
                return True

        return False

    def is_ready(self):
        """
        Return True if the connection is ready.
        False otherwise.
        """
        if self.sock is not None and not self.in_use:
            return True
        else:
            return False

    def mark_used(self):
        """Mark the connection used."""
        self.in_use = True
        self.last_used_time = time.time()

class ConnectionPool(object):

    conn_class = None
    """This must be set by child class."""

    __slots__ = ('host', 'port', 'connections', 'max_connections',
                 'no_of_connections')

    def __init__(self, host, port, max_connections=10):
        self.host = host
        self.port = port
        self.connections = []
        self.no_of_connections = 0
        self.max_connections = max_connections

    def clean_connections(self):
        conns_to_keep = []
        conns_to_orphan = self.no_of_connections - self.max_connections
        for connection in self.connections:
            if conns_to_orphan > 0 and not connection.in_use:
                connection.close()
                conns_to_orphan -= 1
                continue

            if connection.is_usable():
                conns_to_keep.append(connection)
            else:
                connection.close()

        self.connections = conns_to_keep
        self.no_of_connections = len(conns_to_keep)

    def get_connection(self, bind_address):
        """Get a connection if already available in connections or create a new
        one and return."""

        return self.get_ready_connection(bind_address) or \
            self.get_new_connection(bind_address)

    def get_ready_connection(self, bind_address):
        """Return a ready connection"""
        for connection in self.connections:
            if connection.is_ready() and \
               connection.bind_address in bind_address:
                connection.mark_used()
                return connection
        else:
            return None

    def get_new_connection(self, bind_address):
        """Return a new connection"""
        if len(self.connections) >= self.max_connections:
            raise MaxConnectionsLimit(self.host, self.port)
        else:
            try:
                self.no_of_connections += 1
                if ip.is_ipv6(self.host):
                    bind_ip = bind_address[1]
                else:
                    bind_ip = bind_address[0]

                if bind_ip is None:
                    raise IfaceNotCompatible(self.host, self.port)
                new_connection = self.conn_class(self.host, self.port,
                                                 bind_ip)
            except:
                self.no_of_connections -= 1
                raise

            new_connection.mark_used()
            self.connections.append(new_connection)

        return new_connection
