from __future__ import absolute_import, print_function, unicode_literals


def pytest_addoption(parser):
    parser.addoption('--integration', action='store_true',
        help='run integration tests')


# vim:set ts=4 sw=4 expandtab:
