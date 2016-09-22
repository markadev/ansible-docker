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


@integration
def test_build_and_tag(basic_config, image_tracker, docker_client):
    rc = subprocess.call(['ansible-docker',
        '-t', 'testimage',
        '-t', 'testimage:1.0',
        '-t', 'testimage:1.0.5',
        basic_config])
    assert rc == 0

    image_ids = image_tracker.get_image_ids()
    assert len(image_ids) == 1
    image = docker_client.inspect_image(resource_id=image_ids[0])
    image_repotags = sorted(image['RepoTags'])
    assert image_repotags == \
        ['testimage:1.0', 'testimage:1.0.5', 'testimage:latest']


# vim:set ts=4 sw=4 expandtab:
