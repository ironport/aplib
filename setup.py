# $Header: //prod/main/ap/aplib/setup.py#4 $
# Copyright (c) 2008 IronPort Systems, Inc.
# All rights reserved.
# Unauthorized redistribution prohibited.

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
