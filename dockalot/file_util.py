from __future__ import absolute_import, print_function, unicode_literals

import os


def safe_delete(filename):
    """Try to delete a file and ignore all errors"""
    try:
        os.remove(filename)
    except:
        pass


# vim:set ts=4 sw=4 expandtab:
