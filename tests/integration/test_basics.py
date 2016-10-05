from __future__ import absolute_import, print_function, unicode_literals
import subprocess

from .markers import integration


@integration
def test_help():
    rc = subprocess.call(['dockalot', '--help'])
    assert rc == 0


@integration
def test_version():
    rc = subprocess.call(['dockalot', '--version'])
    assert rc == 0
