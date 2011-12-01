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

# $Header: //prod/main/ap/aplib/aplib/net/mask.py#7 $

"""Mask object.

This Mask object is intended to represent either a network mask ("netmask") or
a host mask ("hostmask").  There is a base `Mask` object with two subclasses:
`Mask4` for IPv4 and `Mask6` for IPv6.  See those individual subclasses for
details on the formats of masks supported.

A common use case for this would be in a IPv4 world where the netmask is
specified independently of the IP address.  The netmask could be parsed as a
dotted quad IP address or in hex format.

Noncontiguous masks are NOT supported.
"""

__version__ = '$Revision: #7 $'

from aplib.net import _net
from aplib.net.exceptions import MaskValidationError

class MASK_FORMAT:

    """Static constants for how to format a mask value.

    This is a container for some constants on how to format a mask value.  The
    possible values are:

    - `HEX`: Render as a hexidecimal value starting with "0x".
    - `DOTTED_QUAD`: Render as an IPv4 address.  Only valid for v4 masks.
    - `PREFIX`: Render as a prefix length (such as "24").  This does not
      include the leading slash, even if the object was created with one.
    """

    HEX = 'HEX'
    DOTTED_QUAD = 'DOTTED_QUAD'
    PREFIX = 'PREFIX'

class Mask(object):

    """Base mask class.

    This implements the shared logic between the `Mask4` and `Mask6` objects.
    You should not instantiate it directly.

    This object is intended to be immutable.  It implements the hash method, so
    you can use it as a value in a dictionary.  It also supports comparison
    with other Mask objects, so it can be sorted in a list.

    :IVariables:
        - `mask`: The mask as an integer.
        - `prefixlen`: The prefix length of the mask.  This is zero for
          things like a hostmask.
        - `version`: The address version, either 4 or 6.
        - `WIDTH`: The number of bits in this address type, either 32 or 128.
        - `FULL_MASK`: An integer of the full bitmask for this address type.
        - `render_format`: The format that the mask will be rendered as (see
          `MASK_FORMAT`).
    """

    __slots__ = ('mask', 'prefixlen', 'render_format')

    version = None
    WIDTH = None
    FULL_MASK = None
    _bit_mask_map = None

    def __init__(self, mask):
        """Initialize the Mask object.

        :Parameters:
            - `mask`: The mask.  This can be either an integer or a string. See
              the appropriate subclass docstring for the exact syntax
              supported.

        :Exceptions:
            - `MaskValidationError`: The mask is invalid.
        """
        if isinstance(mask, (int, long)):
            if mask < 0 or mask > self.FULL_MASK:
                raise MaskValidationError(mask)
            self.mask = mask
            try:
                self.prefixlen = self.mask_to_prefixlen(mask)
            except MaskValidationError:
                # Probably a hostmask.
                self.prefixlen = 0
            self.render_format = MASK_FORMAT.HEX
        else:
            self.prefixlen, self.mask, self.render_format = self.parse_mask(mask)
        # Check for non-contiguous mask.
        if not self.is_netmask() and not self.is_hostmask():
            raise MaskValidationError(mask)

    def __int__(self):
        return self.mask

    def __long__(self):
        return self.mask

    def __invert__(self):
        return self.__class__(self.mask ^ self.FULL_MASK)

    def __eq__(self, other):
        try:
            return (self.version == other.version and
                    self.mask == other.mask)
        except AttributeError:
            return NotImplemented

    def __ne__(self, other):
        try:
            return (self.version != other.version or
                    self.mask != other.mask)
        except AttributeError:
            return NotImplemented

    def __lt__(self, other):
        try:
            return (self.version < other.version or
                    self.mask < other.mask)
        except AttributeError:
            return NotImplemented

    def __le__(self, other):
        try:
            return (self.version <= other.version or
                    self.mask <= other.mask)
        except AttributeError:
            return NotImplemented

    def __gt__(self, other):
        try:
            return (self.version > other.version or
                    self.mask > other.mask)
        except AttributeError:
            return NotImplemented

    def __ge__(self, other):
        try:
            return (self.version >= other.version or
                    self.mask >= other.mask)
        except AttributeError:
            return NotImplemented

    def __hash__(self):
        return hash(self.mask)

    # XXX: This doesn't feel like a good idea.  There should be higher-level
    # functions that obviate the need for these.  Think about this.
    #def __lshift__(self, numbits):
    #def __rshift__(self, numbits):
    #def __and__(self, other):
    #def __xor__(self, other):
#    def __or__(self, other):
#        if isinstance(other, BaseIP):
#            return other | self.mask
#        else:
#            return self.__class__(self.mask | int(other))


    def __hex__(self):
        # +2 for leading 0x
        return '%#0*x' % (self.WIDTH/4 + 2, self.mask)

    def __str__(self):
        return self.format()

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                               self.format())

    def format(self, format=None):
        """Render the mask to a string.

        :Parameters:
            - `format`: The format to render it as.  Defaults to the format
              that was used to create the mask object.  See `MASK_FORMAT` for
              the possible values.

        :Return:
            Returns a string representation of the mask.
        """
        if format is None:
            format = self.render_format
        if format == MASK_FORMAT.HEX:
            return hex(self)
        elif format == MASK_FORMAT.DOTTED_QUAD:
            # Avoiding cyclical import.
            import aplib.net.ip
            return aplib.net.ip.IPv4.int_to_str(self.mask)
        elif format == MASK_FORMAT.PREFIX:
            return str(self.prefixlen)
        else:
            raise ValueError(format)

    @classmethod
    def parse_mask(cls, mask):
        """Parse a mask string.

        See the subclass class docstring for details on the format supported.

        :Parameters:
            - `mask`: The mask string to parse.

        :Return:
            Returns a ``(prefixlen, mask_int, format)`` tuple.

        :Exceptions:
            - `MaskValidationError`: The mask is not valid.
        """
        raise NotImplementedError

    @classmethod
    def mask_to_prefixlen(cls, mask):
        """Convert a netmask integer to a prefix length.

        :Parameters:
            - `mask`: The netmask integer to convert.

        :Return:
            Returns the prefix length as an integer.

        :Exceptions:
            - `MaskValidationError`: The mask value is not a valid netmask.
        """
        try:
            return cls._bit_mask_map[mask]
        except KeyError:
            raise MaskValidationError(mask)

    @classmethod
    def prefixlen_to_mask(cls, prefixlen):
        """Convert a prefix length to a netmask integer.

        :Parameters:
            - `prefixlen`: The prefix length.

        :Return:
            Returns the netmask as an integer.

        :Exceptions:
            - `MaskValidationError`: The prefix length is not valid.
        """
        try:
            return ((1 << prefixlen) - 1) << (cls.WIDTH-prefixlen)
        except (ValueError, TypeError):
            raise MaskValidationError(prefixlen)

    def is_netmask(self):
        """Determine if this is a network mask.

        :Return:
            Returns a boolean of whether or not this is a network mask.
        """
        return self.mask in self._bit_mask_map

    def is_hostmask(self):
        """Determine if this is a host mask.

        :Return:
            Returns a boolean of whether or not this is a host mask.
        """
        return (self.mask+1) & self.mask == 0

    @classmethod
    def _parse_prefixlen(cls, mask):
        try:
            prefixlen = int(mask)
        except ValueError:
            raise MaskValidationError(mask)
        mask_int = cls.prefixlen_to_mask(prefixlen)
        return prefixlen, mask_int

class Mask4(Mask):

    """IPv4 mask object.

    The Mask4 object supports three different syntaxes for a mask:

    - Hex value starting with 0x.  Example '0xffffff00'.
    - Prefix length as a string.  Example '/24' or '24', '/16' or '16'.
    - Dotted quad IP address.  Example '255.255.255.0'.

    See `Mask` docstring for more detail.
    """

    __slots__ = ()

    version = 4
    WIDTH = 32
    FULL_MASK = 2**32 - 1

    _bit_mask_map = {}
    for _x in xrange(33):
        _bit_mask_map[(2**_x - 1) << (32-_x)] = _x

    @classmethod
    def parse_mask(cls, mask):
        if mask.startswith('0x'):
            if len(mask) != 10:
                raise MaskValidationError(mask)
            else:
                try:
                    mask_int = int(mask, 16)
                    format = MASK_FORMAT.HEX
                except ValueError:
                    raise MaskValidationError(mask)
        elif mask.startswith('/'):
            format = MASK_FORMAT.PREFIX
            prefixlen, mask_int = cls._parse_prefixlen(mask[1:])
        else:
            try:
                prefixlen, mask_int = cls._parse_prefixlen(mask)
                format = MASK_FORMAT.PREFIX
            except MaskValidationError:
                try:
                    mask_int = _net.parse_ipv4(mask)
                    format = MASK_FORMAT.DOTTED_QUAD
                except ValueError:
                    raise MaskValidationError(mask)

        # We don't allow non-contiguous netmasks.
        try:
            prefixlen = Mask4._bit_mask_map[mask_int]
        except KeyError:
            raise MaskValidationError(mask)

        return prefixlen, mask_int, format


class Mask6(Mask):

    """IPv6 mask object.

    The Mask6 object supports only one syntax for a mask. The value may start
    with a slash and must end with a prefix length. For example '/32', '32',
    '/128' or '/128' are valid mask values. The value must be a string.

    See `Mask` docstring for more detail.
    """

    __slots__ = ()

    version = 6
    WIDTH = 128
    FULL_MASK = 2**128 - 1

    _bit_mask_map = {}
    for _x in xrange(129):
        _bit_mask_map[(2**_x - 1) << (128-_x)] = _x

    @classmethod
    def parse_mask(cls, mask):
        if mask.startswith('/'):
            mask = mask[1:]
        prefixlen, mask_int = cls._parse_prefixlen(mask)
        return prefixlen, mask_int, MASK_FORMAT.PREFIX

