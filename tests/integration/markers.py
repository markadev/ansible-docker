from __future__ import absolute_import, print_function, unicode_literals
import pytest


integration = pytest.mark.skipif(
    not pytest.config.getoption('--integration'),
    reason='need --integration option to run'
)


# vim:set ts=4 sw=4 expandtab:
