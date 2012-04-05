import sys

"""
Usage:

import breaker

"""

def rdb_on_exception(type, value, tb):
    if hasattr(sys, 'ps1') or not sys.stderr.isatty():
        sys.__excepthook__(type, value, tb)
    else:
        from rdb import Rdb
        Rdb().post_mortem(tb)

sys.excepthook = rdb_on_exception