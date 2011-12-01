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

# $Header: //prod/main/ap/aplib/aplib/net/exceptions.py#2 $

"""Network package exceptions."""

__version__ = '$Revision: #2 $'

class Error(Exception):

    """Base exception for all network package exceptions."""

    def __str__(self):
        return self.__repr__()

class IPValidationError(Error):

    """IP address is invalid.

    :IVariables:
        - `address`: The address that is invalid.  In some circumstances this
          may be a string and in others it may be an integer.
    """

    def __init__(self, address):
        Exception.__init__(self)
        self.address = address

    def __repr__(self):
        return '<IPValidationError %s>' % (self.address,)

class MaskValidationError(Error):

    """Mask is invalid.

    :IVariables:
        - `mask`: The mask that is invalid.  In some circumstances this
          may be a string and in others it may be an integer.
    """

    def __init__(self, mask):
        Exception.__init__(self)
        self.mask = mask

    def __repr__(self):
        return '<MaskValidationError %s>' % (self.mask,)
