from __future__ import absolute_import, print_function, unicode_literals
import pytest
import subprocess

from .markers import integration


@pytest.fixture
def test_net(docker_client):
    """Create a user-defined network. Returns the network name."""
    net_name = 'dockalot-inttest'
    docker_client.create_network(net_name, driver='bridge')

    yield net_name

    docker_client.remove_network(net_name)


@integration
def test_build_on_network(basic_config, image_tracker, test_net):
    """Attach the build container to a user-defined network"""
    subprocess.check_call(['dockalot', '--network', test_net, basic_config])
    images = image_tracker.get_image_ids()
    assert len(images) == 1
