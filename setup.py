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

from distutils.core import setup
from Cython.Distutils import build_ext
from Cython.Distutils.extension import Extension

def CythonExtension(*args, **kwargs):

    depends = kwargs.setdefault('depends', [])
    # Doesn't truely apply to everything, but most of the modules import these.
    depends.extend(['pyrex/python.pxi',
                    'pyrex/libc.pxd',
                    'pyrex/pyrex_helpers.pyx',
                    'include/pyrex_helpers.h',
                   ]
                  )

    include_dirs = kwargs.setdefault('include_dirs', [])
    include_dirs.append('include')

    pyrex_include_dirs = kwargs.setdefault('pyrex_include_dirs', [])
    pyrex_include_dirs.append('pyrex')

    return Extension(*args, **kwargs)

setup (
    name='aplib',
    version='1.0.0-000',
    packages=['aplib', 'aplib/net', 'aplib/tsc_time'],
    ext_modules=[
        # Please keep this list alphabetized.
        CythonExtension ('aplib.net._net', ['aplib/net/aplib.net._net.pyx']),
        CythonExtension ('aplib.oserrors', ['aplib/aplib.oserrors.pyx']),
    ],
    cmdclass={'build_ext': build_ext},
)
