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

"""Unittests for tb module."""

__version__ = '$Revision: #1 $'

import unittest
from aplib import tb

class Test(unittest.TestCase):

    def test_stack_string(self):
        ss = tb.stack_string()
        if not ss.startswith('[test_tb.py test_stack_string|16] '):
            self.fail('Did not start correctly: %r' % (ss,))

    def test_traceback_string(self):
        try:
            raise ValueError(3)
        except ValueError:
            ts = tb.traceback_string()
            # Don't want to be too strict with the checks.
            if "('test_tb.py test_traceback_string|22'" not in ts:
                self.fail('No line found: %r' % (ts,))
            if 'ValueError' not in ts:
                self.fail('No value error: %r' % (ts,))
            if "'3'" not in ts:
                self.fail('Exception value not found: %r' % (ts,))
            if '[test_tb.py test_traceback_string|22]' not in ts:
                self.fail('Stack string not found: %r' % (ts,))

if __name__ == '__main__':
    unittest.main()
