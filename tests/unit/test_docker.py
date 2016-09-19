from __future__ import absolute_import, print_function, unicode_literals
import pytest

from ansible_docker.config import ConfigurationError
from ansible_docker.docker import validate_docker_config


@pytest.mark.parametrize('config', [
    {'docker': {'base_image': 'a'}},
    {'docker': {'base_image': 'a', 'build_volumes': ['v1']}},
    {'docker': {'base_image': 'a', 'cmd': ['bash']}},
    {'docker': {'base_image': 'a', 'entrypoint': ['/start.sh']}},
    {'docker': {'base_image': 'a', 'expose_ports': [123, 345]}},
    {'docker': {'base_image': 'a', 'volumes': ['v1', 'v2']}},
    {'docker': {'base_image': 'a', 'workdir': '/root'}},
])
def test_validate_docker_config_ok(config):
    """Validate valid docker configs"""
    validate_docker_config(config)


@pytest.mark.parametrize('config', [
    {},  # missing 'docker' section
    {'docker': 'not_a_dict'},  # 'docker' is not a dict
    {'docker': {}},  # missing base_image
    {'docker': {'base_image': ['not', 'a', 'string']}},
    {'docker': {'base_image': 'a', 'build_volumes': 'not_a_list'}},
    {'docker': {'base_image': 'a', 'cmd': 'not_a_list'}},
    {'docker': {'base_image': 'a', 'entrypoint': 'not_a_list'}},
    {'docker': {'base_image': 'a', 'expose_ports': ['nan', 'nan']}},
    {'docker': {'base_image': 'a', 'volumes': 'not_a_list'}},
    {'docker': {'base_image': 'a', 'workdir': ['not', 'a', 'string']}},
])
def test_validate_docker_config_invalid(config):
    """Validate valid docker configs"""
    with pytest.raises(ConfigurationError):
        validate_docker_config(config)


# vim:set ts=4 sw=4 expandtab:
