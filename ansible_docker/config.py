from __future__ import absolute_import, print_function, unicode_literals

from functools import partial
import six


class ConfigurationError(Exception):
    pass


def _convert_to_string(value):
    if isinstance(value, six.string_types) or \
            isinstance(value, six.integer_types):
        return six.text_type(value)
    raise ValueError('Cannot convert value to a string')


def _convert_list(element_type, value):
    if not isinstance(value, list):
        raise ValueError('Cannot convert value to a list')
    return [element_type[1](v) for v in value]


TYPE_NUMBER = ('number', int)
TYPE_STRING = ('string', _convert_to_string)
TYPE_LIST_STRING = ('list of strings', partial(_convert_list, TYPE_STRING))
TYPE_LIST_NUMBER = ('list of numbers', partial(_convert_list, TYPE_NUMBER))


def validate_config_type(config, name, type, prefix='', required=False):
    """
    :param type: A tuple of (type_name, type_converter)
    """
    value = config.get(name)
    if value is not None:
        try:
            converted_value = type[1](value)
        except:
            raise ConfigurationError(
                "Configuration value '{}{}' is not a {}"
                .format(prefix, name, type[0]))
        config[name] = converted_value
        return (converted_value, prefix + name + '/')
    elif required:
        raise ConfigurationError("Configuration value '{}{}' is missing"
            .format(prefix, name))
    return (None, None)


# vim:set ts=4 sw=4 expandtab:
