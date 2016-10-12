from __future__ import absolute_import, print_function, unicode_literals
import os
import subprocess

from .markers import integration


@integration
def test_build_basic(basic_config, image_tracker, docker_client):
    subprocess.check_call(['dockalot', basic_config])
    images = image_tracker.get_image_ids()
    assert len(images) == 1

    # Check the image metadata is correct
    image_info = docker_client.inspect_image(resource_id=images[0])
    assert image_info['RepoTags'] == []
    assert image_info['Config']['Entrypoint'] == ['/entrypoint.py']


@integration
def test_build_failure(failing_config, image_tracker):
    retry_file_name = os.path.join(os.path.dirname(failing_config),
        ".tmp-{}.retry".format('failing'))

    rc = subprocess.call(['dockalot', failing_config])
    assert rc != 0

    # No image should have been created
    images = image_tracker.get_image_ids()
    assert len(images) == 0

    # The .retry file created by Ansible should be deleted
    assert not os.path.exists(retry_file_name)


@integration
def test_build_and_tag(basic_config, image_tracker, docker_client):
    subprocess.check_call(['dockalot',
        '-t', 'testimage',
        '-t', 'testimage:1.0',
        '-t', 'testimage:1.0.5',
        basic_config])

    image_ids = image_tracker.get_image_ids()
    assert len(image_ids) == 1
    image = docker_client.inspect_image(resource_id=image_ids[0])
    image_repotags = sorted(image['RepoTags'])
    assert image_repotags == \
        ['testimage:1.0', 'testimage:1.0.5', 'testimage:latest']


@integration
def test_build_complex(complex_config, image_tracker, docker_client):
    subprocess.check_call(['dockalot', complex_config])
    images = image_tracker.get_image_ids()
    assert len(images) == 1

    # Check the image metadata is correct
    image_info = docker_client.inspect_image(resource_id=images[0])
    assert sorted(image_info['RepoTags']) == \
        ['pythonapp:1.0', 'pythonapp:latest']
    assert image_info['Config']['Entrypoint'] == ['/app/entrypoint.py']
    assert 'APP_PATH=/app/bin' in image_info['Config']['Env']
    assert 'DATASETS=1000 2000 3000' in image_info['Config']['Env']
    assert image_info['Config']['Cmd'] == ['param1', 'param2']
    assert image_info['Config']['ExposedPorts'] == {'10000/tcp': {}}
    assert image_info['Config']['Labels'] == {
        'net.primeletters.test': 'enabled',
        'net.primeletters.version': '1'}
    assert image_info['Config']['WorkingDir'] == '/app'
    assert image_info['Config']['Volumes'] == {'/data': {}}


# vim:set ts=4 sw=4 expandtab:
