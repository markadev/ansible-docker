from __future__ import absolute_import, print_function, unicode_literals

import argparse
from collections import Mapping
import six


class ConfigurationError(Exception):
    pass


class ArgSaverAction(argparse.Action):
    """argparse action to save the option and its value in a list"""
    def __call__(self, parser, namespace, values, option_string=None):
        arglist = list(getattr(namespace, self.dest) or [])
        arglist.append(option_string)
        if self.nargs is not None:
            arglist.extend(values)
        else:
            arglist.append(values)
        setattr(namespace, self.dest, arglist)


def string_importer(value, name):
    if isinstance(value, six.string_types) or \
            isinstance(value, six.integer_types) or \
            isinstance(value, bool):
        return six.text_type(value)
    raise ConfigurationError("Configuration value '{}' is not a string"
        .format('.'.join(name)))


def integer_importer(value, name):
    try:
        return int(value)
    except:
        raise ConfigurationError("Configuration value '{}' is not an integer"
            .format('.'.join(name)))


def enum_importer(value_set):
    """
    Returns an importer function for enumerations with the given allowed
    set of values.
    """
    def _importer(value, name):
        lower_value = string_importer(value, name).lower()
        if lower_value in value_set:
            return lower_value

        raise ConfigurationError("Configuration value '{}' is not one of "
            "the expected values [ {} ]"
            .format('.'.join(name), ', '.join(value_set)))
    return _importer


def string_list_importer(value, name):
    if isinstance(value, list):
        return [string_importer(v, name + [str(i)])
            for i, v in enumerate(value)]
    raise ConfigurationError("Configuration value '{}' is not a list"
        .format('.'.join(name)))


def integer_list_importer(value, name):
    if isinstance(value, list):
        return [integer_importer(v, name + [str(i)])
            for i, v in enumerate(value)]
    raise ConfigurationError("Configuration value '{}' is not a list"
        .format('.'.join(name)))


def string_dict_importer(value, name):
    if isinstance(value, dict):
        return dict((six.text_type(k), string_importer(v, name + [k]))
            for k, v in six.iteritems(value))
    raise ConfigurationError("Configuration value '{}' is not a dict"
        .format('.'.join(name)))


def docker_section_importer(value, name):
    return DockerConfig(value, name)


class BaseConfigDict(Mapping):
    def __init__(self):
        self.items = {}

    def import_config_item(self, key, config_dict, importer=string_importer,
            required=False, prefix=None, default=None):
        """
        Imports the configuration from config_dict, translating it to the
        proper internal format using the given importer.
        """
        full_name = [key] if prefix is None else (prefix + [key])

        value = config_dict.get(key)
        if value is not None:
            imported_value = importer(value, name=full_name)
            self.items[key] = imported_value
        elif required:
            raise ConfigurationError("Configuration value for '{}' is missing"
                .format('.'.join(full_name)))
        elif default is not None:
            self.items[key] = default

    def __len__(self):
        return len(self.items)

    def __getitem__(self, key):
        return self.items[key]

    def __iter__(self):
        return iter(self.items)


class DockerConfig(BaseConfigDict):
    """Docker image configuration section"""
    def __init__(self, config_dict, prefix):
        super(DockerConfig, self).__init__()

        # Required parameters
        self.import_config_item('base_image', config_dict, prefix=prefix,
            required=True)

        # Optional parameters
        self.import_config_item('cmd', config_dict,
            importer=string_list_importer, prefix=prefix)
        self.import_config_item('entrypoint', config_dict,
            importer=string_list_importer, prefix=prefix)
        self.import_config_item('env', config_dict,
            importer=string_dict_importer, prefix=prefix)
        self.import_config_item('expose_ports', config_dict,
            importer=integer_list_importer, prefix=prefix)
        self.import_config_item('labels', config_dict,
            importer=string_dict_importer, prefix=prefix)
        self.import_config_item('tags', config_dict,
            importer=string_list_importer, prefix=prefix)
        self.import_config_item('volumes', config_dict,
            importer=string_list_importer, prefix=prefix)
        self.import_config_item('workdir', config_dict, prefix=prefix)

    def merge_command_line_args(self, args):
        if args.tag is not None:
            self.items['tags'] = args.tag
        if args.label is not None:
            new_label_list = map(lambda l: l.split('=', 1), args.label)
            new_labels = dict((k.strip(), v.strip())
                for k, v in new_label_list)
            self.items['labels'] = new_labels


class Config(BaseConfigDict):
    """Top-level configuration dictionary"""
    def __init__(self, config_dict):
        super(Config, self).__init__()

        self.import_config_item('inventory_groups', config_dict,
            importer=string_list_importer, required=False)

        self.import_config_item('preparation_commands', config_dict,
            importer=string_list_importer, required=False)
        self.import_config_item('cleanup_commands', config_dict,
            importer=string_list_importer, required=False)

        self.import_config_item('docker', config_dict,
            importer=docker_section_importer, required=True)

    def merge_command_line_args(self, args):
        """
        Merge the values specified on the command line into the configuration.
        """
        self.items['always_pull'] = args.pull
        if args.ansible_args is not None:
            self.items['ansible_args'] = args.ansible_args
        self.items['docker'].merge_command_line_args(args)


# vim:set ts=4 sw=4 expandtab:
