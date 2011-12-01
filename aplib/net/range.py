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

# $Header: //prod/main/ap/aplib/aplib/net/range.py#2 $

"""Objects for handling a range of IP addresses.

The `IPRange` object and its subclasses represents a range of contiguous IP
addresses.  The `Prefix` subclass represents a network block (using prefix
notation like '1.2.3.0/24').  The `IPGlob` object represents a more general
range of IP's that may not necessarily fit into a network block.

Future
======
- Create an object that represents a "set" of a bunch of different range
  objects. (ala TCP Wrappers rules).  This should be very extensible to be able
  to support other object types (hostnames, senderbase organization ID,
  IronPort HAT, etc.).

- Given range, divide into subnets.  (See IP.subnet)

- Given a Prefix, get the supernet.

- Given a range, subtract a range (or IP) from it and return a list of ranges.
"""

__version__ = '$Revision: #2 $'

from aplib.net.exceptions import IPValidationError

def _slice_indices(slice, length):
    """Compute slice indices.

    This is a copy of PySlice_GetIndicesEx that can handle values greater than
    Py_ssize_t (like IPv6 or greater than 2**31 IPv4).
    """
    if slice.step == None:
        step = 1
    else:
        step = slice.step

    if step < 0:
        defstart = length-1
        defstop = 0
    else:
        defstart = 0
        defstop = length

    if slice.start == None:
        start = defstart
    else:
        start = slice.start
        if start < 0:
            start += length
        if start < 0:
            start = -1 if step < 0 else 0
        if start >= length:
            start = length-1 if step < 0 else length

    if slice.stop == None:
        stop = defstop
    else:
        stop = slice.stop
        if stop < 0:
            stop += length
        if stop < 0:
            stop = -1 if step < 0 else 0
        if stop >= length:
            stop = length-1 if step < 0 else length

    # Don't need slicelength for now.
#    if ((step < 0 and stop > start) or
#        (step > 0 and start >= stop)
#       ):
#        slicelength = 0
#    elif step < 0:
#        slicelength = (stop-start+1)/step+1
#    else:
#        slicelength = (stop-start-1)/step+1
    return start, stop, step

class IPRange(object):

    """IPRange object.

    This represents a contiguous range of IP addresses.

    This object is intended to be immutable.  It implements the hash method, so
    you can use it as a value in a dictionary.

    Ranges supports "contains".  So for example, you can do this::

        >>> IP('1.2.3.4') in Prefix('1.2.3.0/24')
        True

    Ranges support some sequence operations.  You can access individual items
    in a range::

        >>> Prefix('1.2.3.0/24')[10]
        IPv4('1.2.3.10')

    Slice syntax is also supported, in which case it returns an iterator to
    handle large ranges.  You can also iterate over a range to visit every IP
    address.  See `IPRange.iterator` for a direct way to access the iterator.
    Ranges do NOT support __len__ because it does not allow values greater that
    2**31, use the `size` method instead.

    Ranges support comparison operators.  Ranges that begin before other ranges
    are considered less than those other ranges. If two ranges start at the
    same IP, then the less-specific network is considered less than the
    more-specific network (networks with a smaller prefix length are less than
    those with a greater prefix length).  In other words, ranges of a greater
    size are less than those of a smaller size.

    :IVariables:
        - `first`: The first IP address object.
        - `last`: The last IP address object.
    """

    __slots__ = ('first', 'last')

    def __init__(self, first, last):
        """Initialize a range object.

        The IP type (v4 or v6) of first and last must be the same.

        :Parameters:
            - `first`: The first IP object.
            - `last`: The last IP object.
        """
        self.first = first
        self.last = last
        assert first.__class__ == last.__class__
        if self.last < self.first:
            raise IPValidationError('Start IP (%r) > End IP (%r)' % (first, last))

    def size(self):
        """Get the size of the range.

        This returns the number IP's in the range including the first and last
        element. A range of 1 IP has a size of 1.

        :Return:
            Returns the size as an integer.
        """
        return int(self.last) - int(self.first) + 1

    def is_adjacent(self, other):
        """Determine if another range is adjacent to this one.

        Adjacent means they border one another (and do not overlap).

        :Parameters:
            - `other`: The IPRange to compare against this one.

        :Return:
            Returns True if the ranges are adjacent, False otherwise.
        """
        try:
            if self.first == other.last+1:
                return True
        except IPValidationError:
            pass
        try:
            if self.last == other.first-1:
                return True
        except IPValidationError:
            pass

        return False

    def overlaps(self, other):
        """Determine if another range overlaps with this one.

        :Parameters:
            - `other`: The IPRange to compare against this one.

        :Return:
            Returns True if the other range overlaps with this one, False
            otherwise.
        """
        if self.first <= other.last <= self.last:
            return True
        if self.first <= other.first <= self.last:
            return True
        return False

    def __getitem__(self, index):
        size = self.size()
        if isinstance(index, (int, long)):
            if index < 0:
                index += size
            if index < 0 or index >= size:
                raise IndexError()
            return self.first.__class__(int(self.first) + index)
        elif isinstance(index, slice):
            start, stop, step = _slice_indices(index, self.size())
            return self.iterator(start, stop, step)
        else:
            raise TypeError(index)

    def __iter__(self):
        return self.iterator()

    def iterator(self, start=0, stop=None, step=1):
        """Return an iterator to visit IP addresses in the range.

        This supports standard Python slice notation.  Start, stop, and step
        values can be negative.

        :Parameters:
            - `start`: The starting index.
            - `stop`: The stopping index.  Defaults to the end of the range.
            - `step`: The step value.

        :Return:
            Returns an iterator that returns IP address objects.
        """
        start, stop, step = _slice_indices(slice(start, stop, step), self.size())
        index = int(self.first) + start
        last = int(self.first) + stop
        while index < last:
            yield self.first.__class__(index)
            index += step

    def __contains__(self, other):
        return self.first <= other <= self.last

    def is_subnet(self, other):
        """Determine if another range is a subnet of this range.

        :Parameters:
            - `other`: The IPRange object to compare against.

        :Return:
            Returns True if `other` is a subnet of this range, False otherwise.
        """
        return self.first >= other.first and self.last <= other.last

    def is_supernet(self, other):
        """Determine if another range is a supernet of this range.

        :Parameters:
            - `other`: The IPRange object to compare against.

        :Return:
            Returns True if `other` is a supernet of this range, False otherwise.
        """
        return self.first <= other.first and self.last >= other.last

    def __hash__(self):
        return hash((self.first, self.last))

    def __str__(self):
        return '%s-%s' % (self.first, self.last)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__,
                               self.first, self.last)

    def __eq__(self, other):
        if isinstance(other, IPRange):
            return self.first == other.first and self.last == other.last
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, IPRange):
            return self.first != other.first or self.last != other.last
        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, IPRange):
            return (self.first, other.size()) < (other.first, self.size())
        elif isinstance(other, aplib.net.ip.BaseIP):
            return self.first < other
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, IPRange):
            return (self.first, other.size()) <= (other.first, self.size())
        elif isinstance(other, aplib.net.ip.BaseIP):
            return self.first <= other
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, IPRange):
            return (self.first, other.size()) > (other.first, self.size())
        elif isinstance(other, aplib.net.ip.BaseIP):
            return self.first > other
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, IPRange):
            return (self.first, other.size()) >= (other.first, self.size())
        elif isinstance(other, aplib.net.ip.BaseIP):
            return self.first > other
        else:
            return NotImplemented


class Prefix(IPRange):

    """Prefix address range.

    This IPRange type supports prefix-style notation for both IPv4 or IPv6.
    For example::

        >>> Prefix('1.2.3.4/24')
        Prefix('1.2.3.0/24')
        >>> Prefix('2001:db8::/32')
        Prefix('2001:db8::/32')

    Notice that the host bits of '1.2.3.4' were stripped in the example.
    """

    __slots__ = ('prefixlen',)

    def __init__(self, address):
        """Initialize a Prefix object.

        :Parameters:
            - `address`: The prefix address.  This can either be an IP address
              object or a string.

        :Exceptions:
            - `IPValidationError`: The address is not valid.
        """
        if isinstance(address, basestring):
            address = aplib.net.ip.IP(address)
        self.prefixlen = address.prefixlen
        first = address.__class__(address.ip & address.netmask_int)
        last = address.broadcast
        super(Prefix, self).__init__(first, last)

    def __str__(self):
        return '%s/%i' % (self.first, self.prefixlen)

    def __repr__(self):
        return '%s(\'%s\')' % (self.__class__.__name__, self)

class IPGlob(IPRange):

    """IP glob address range.

    This IPRange type supports various different range and "glob" syntaxes.
    This class only works with IPv4 address, IPv6 is not supported.

    The variants supported are:

    - Single IP address:
        - ``1.2.3.4``

    - Classful wildcards:
        - ``1.2.3.*`` ``1.2.*.*``
        - Not all octets are required like ``1.2.*``.
        - ``*`` or ``*.*.*.*`` match all IPv4 addresses.

    - Classful portions:
        - ``1`` means ``1.*.*.*``
        - ``1.2.3`` means ``1.2.3.*``
        - Partial values can end with an optional dot like ``1.2.``.

    - Dash ranges (only asterisks are allowed after a range):
        - ``1.2.3.0-10``
        - ``1.2-3.*.*``
        - ``1.2-3.``
        - ``1.2-3``
    """

    __slots__ = ()

    def __init__(self, address):
        first, last = self._parse(address)
        super(IPGlob, self).__init__(first, last)

    @staticmethod
    def _parse(address):
        parts = address.split('.')
        if len(parts) > 4:
            raise IPValidationError(address)
        if parts[-1] == '':
            parts[-1] = '*'
        if '' in parts:
            raise IPValidationError(address)
        if len(parts) < 4:
            parts.extend(['*']*(4-len(parts)))

        first = []
        last = []
        stars_only = False

        def int_part(x):
            try:
                x = int(x)
            except ValueError:
                raise IPValidationError(address)
            if x < 0 or x > 255:
                raise IPValidationError(address)
            return str(x)

        for part in parts:
            if part == '*':
                first.append('0')
                last.append('255')
                stars_only = True
            elif stars_only:
                raise IPValidationError(address)
            elif '-' in part:
                x, y = part.split('-', 1)
                first.append(int_part(x))
                last.append(int_part(y))
                stars_only = True
            else:
                x = int_part(part)
                first.append(part)
                last.append(part)

        IPv4 = aplib.net.ip.IPv4
        return IPv4('.'.join(first)), IPv4('.'.join(last))


# Putting this at the bottom is a bit of a hack to work around cyclical
# import issues.
import aplib.net.ip
