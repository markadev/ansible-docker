from __future__ import absolute_import, print_function, unicode_literals
import pytest

from ansible_docker.config import ConfigurationError, validate_config_type, \
    TYPE_NUMBER, TYPE_STRING, TYPE_LIST_NUMBER, TYPE_LIST_STRING


def test_validate_config_type_required():
    """Tests validate_config_type 'required' parameter"""
    config = {}
    value = validate_config_type(config, 'key1', type=TYPE_STRING,
        required=False)
    assert value == (None, None)

    with pytest.raises(ConfigurationError):
        validate_config_type(config, 'key1', type=TYPE_STRING,
            required=True)


@pytest.mark.parametrize("value,type,expected_value", [
    (123, TYPE_NUMBER, 123),
    (123L, TYPE_NUMBER, 123),
    ('123', TYPE_NUMBER, 123),
    ('abcd', TYPE_STRING, 'abcd'),
    ([], TYPE_LIST_NUMBER, []),
    ([1, 2L, '3'], TYPE_LIST_NUMBER, [1, 2, 3]),
    ([1, 2L, '3'], TYPE_LIST_STRING, ['1', '2', '3']),
])
def test_validate_config_type_ok(value, type, expected_value):
    """Tests that validation succeeds with different types"""
    config = {'key1': value}
    prefix = 'section1/'
    v = validate_config_type(config, 'key1', type=type, prefix=prefix)
    assert v == (expected_value, prefix + 'key1/')


@pytest.mark.parametrize("value,type", [
    ('abcd', TYPE_NUMBER),
    (['a', 'b'], TYPE_NUMBER),
    ({'a': '1'}, TYPE_NUMBER),
    (['a', 'b'], TYPE_STRING),
    ({'a': '1'}, TYPE_STRING),
    ('abcd', TYPE_LIST_NUMBER),
    (['a', 'b'], TYPE_LIST_NUMBER),
    (123, TYPE_LIST_NUMBER),
    ('abcd', TYPE_LIST_STRING),
    (123, TYPE_LIST_STRING),
    ([1, 2, []], TYPE_LIST_STRING),
])
def test_validate_config_type_invalid(value, type):
    """
    Tests that validation fails with values that are incompatible with
    the type.
    """
    with pytest.raises(ConfigurationError):
        config = {'key1': value}
        validate_config_type(config, 'key1', type=type)


# vim:set ts=4 sw=4 expandtab:
