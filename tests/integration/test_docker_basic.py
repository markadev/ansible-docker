from __future__ import absolute_import, print_function, unicode_literals
import subprocess

from .markers import integration


@integration
def test_help():
    rc = subprocess.call(['ansible-docker', '--help'])
    assert rc == 0


@integration
def test_build_basic(basic_config, image_tracker):
    rc = subprocess.call(['ansible-docker', basic_config])
    assert rc == 0


# vim:set ts=4 sw=4 expandtab:
