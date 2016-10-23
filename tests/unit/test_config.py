from __future__ import absolute_import, print_function, unicode_literals
import mock
import pytest

from dockalot.config import ConfigurationError, Config, DockerConfig, \
    string_importer, integer_importer, enum_importer, \
    string_list_importer, integer_list_importer, \
    string_dict_importer


# Class for holding fake command line args parsed from argparse
class FakeArgs(object):
    def __init__(self, args):
        self.tag = args.get('tag', None)
        self.label = args.get('label', None)
        self.env = args.get('env', None)


@pytest.mark.parametrize('importer,input,expected_value', [
    (string_importer, 'abc', 'abc'),
    (string_importer, 123, '123'),
    (string_importer, True, 'True'),
    (integer_importer, 123, 123),
    (integer_importer, '123', 123),
    (enum_importer(['aaa', 'bbb']), 'aaa', 'aaa'),
    (enum_importer(['aaa', 'bbb']), 'bbb', 'bbb'),
    (enum_importer(['aaa', 'bbb']), 'AAa', 'aaa'),
    (string_list_importer, [], []),
    (string_list_importer, [1, '2', False], ['1', '2', 'False']),
    (integer_list_importer, [], []),
    (integer_list_importer, [1, '2'], [1, 2]),
    (string_dict_importer, {}, {}),
    (string_dict_importer, {'a': 'abcd', 'b': 12}, {'a': 'abcd', 'b': '12'}),
])
def test_importer_valid(importer, input, expected_value):
    """Test low-level importers successfully convert values"""
    assert importer(input, ['test']) == expected_value


@pytest.mark.parametrize('importer,input', [
    (string_importer, ['abcd']),
    (string_importer, {'a': 1}),
    (string_importer, object()),
    (integer_importer, 'abcd'),
    (integer_importer, ['1']),
    (integer_importer, {'a': '1'}),
    (enum_importer(['aaa', 'bbb']), 'xxx'),
    (string_list_importer, 'not_a_list'),
    (string_list_importer, ['a', 'b', []]),
    (integer_list_importer, 'not_a_list'),
    (integer_list_importer, ['abcd']),
    (string_dict_importer, {'a': ['abcd', 'efgh']}),
])
def test_importer_invalid(importer, input):
    """Test low-level importers successfully reject bad values"""
    with pytest.raises(ConfigurationError):
        importer(input, ['test'])


@pytest.mark.parametrize('config_dict,key,expected_value', [
    ({}, 'docker', {}),
    ({'inventory_groups': ['a']}, 'inventory_groups', ['a']),
    ({'preparation_commands': ['xxx']}, 'preparation_commands', ['xxx']),
    ({'cleanup_commands': ['yyy']}, 'cleanup_commands', ['yyy']),
])
@mock.patch('dockalot.config.docker_section_importer', return_value={})
def test_Config_validation(m, config_dict, key, expected_value):
    """Tests successful validation of top-level configuration items"""
    # Add a fake 'docker' section because it is required
    config_dict['docker'] = {}

    cfg = Config(config_dict)
    assert cfg[key] == expected_value


@pytest.mark.parametrize('config_dict,key,expected_value', [
    ({'base_image': 'debian'},
        'base_image', 'debian'),
    ({'cmd': ['bash'], 'base_image': 'debian'},
        'cmd', ['bash']),
    ({'entrypoint': ['/start.sh'], 'base_image': 'debian'},
        'entrypoint', ['/start.sh']),
    ({'env': {'A': 'abc'}, 'base_image': 'debian'},
        'env', {'A': 'abc'}),
    ({'expose_ports': [123, 345], 'base_image': 'debian'},
        'expose_ports', [123, 345]),
    ({'labels': {'a': 'wee', 'b': 2}, 'base_image': 'debian'},
        'labels', {'a': 'wee', 'b': '2'}),
    ({'volumes': ['v1', 'v2'], 'base_image': 'debian'},
        'volumes', ['v1', 'v2']),
    ({'workdir': '/root', 'base_image': 'debian'},
        'workdir', '/root'),
])
def test_DockerConfig_validation(config_dict, key, expected_value):
    """
    Tests successful validation of items in the docker image configuration
    """
    c = DockerConfig(config_dict, prefix=['docker'])
    assert c[key] == expected_value


@pytest.mark.parametrize('config_dict', [
    {},  # Missing 'base_image'
    {'base_image': ['not', 'a', 'string']},
    {'base_image': 'debian', 'cmd': 'not_a_list'},
    {'base_image': 'debian', 'entrypoint': 'not_a_list'},
    {'base_image': 'debian', 'env': 'not_a_dict'},
    {'base_image': 'debian', 'expose_ports': ['nan', 'nan']},
    {'base_image': 'debian', 'labels': 'not_a_dict'},
    {'base_image': 'debian', 'volumes': 'not_a_list'},
])
def test_DockerConfig_validation_failure(config_dict):
    with pytest.raises(ConfigurationError):
        DockerConfig(config_dict, prefix=['docker'])


@pytest.mark.parametrize('config_dict,arg_dict,item_name,expected_value', [
    # Tags specified on the command line replace all tags from the config
    ({'tags': ['a', 'b']}, {}, 'tags', ['a', 'b']),
    ({'tags': ['a', 'b']}, {'tag': ['c']}, 'tags', ['c']),

    # Labels specified on the command line replace all labels in the config
    ({'labels': {'name': 'foo'}}, {}, 'labels', {'name': 'foo'}),
    ({'labels': {'name': 'foo'}}, {'label': ['desc=frob']},
        'labels', {'desc': 'frob'}),
])
def test_DockerConfig_merge_command_line_args(config_dict, arg_dict,
        item_name, expected_value):
    """
    Tests DockerConfig.merge_command_line_args

    With a given configuration in `config_dict` and command line arguments
    in `arg_dict`, after merging in the command line args we'll expect
    the given `item_name` in the configuration to be equal to the
    `expected_value`.
    """
    config_dict['base_image'] = 'debian'  # Required parameter for DockerConfig
    docker_config = DockerConfig(config_dict, prefix=[])
    args = FakeArgs(arg_dict)

    docker_config.merge_command_line_args(args)
    assert docker_config[item_name] == expected_value


# vim:set ts=4 sw=4 expandtab:
