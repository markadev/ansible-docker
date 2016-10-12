from __future__ import absolute_import, print_function, unicode_literals
import docker
import mock
import pytest

from dockalot.docker import parse_args, \
    pull_base_image, make_container, run_command_list, commit_image, \
    tag_image


@pytest.fixture
def mock_docker_client():
    return mock.create_autospec(docker.Client)


@pytest.mark.parametrize('args,attrname,expected_value', [
    ([], 'configfile', 'fake_configfile.yml'),
    (['--ask-vault-pass'], 'ansible_args', ['--ask-vault-pass']),
    (['-e', 'v1=a', '-e', 'v2=b'], 'ansible_args',
        ['-e', 'v1=a', '-e', 'v2=b']),
    (['--vault-password-file', 'passwd.txt'], 'ansible_args',
        ['--vault-password-file', 'passwd.txt']),
])
def test_base_parse_args(args, attrname, expected_value):
    """Verify parsing of the base command line args"""
    result = parse_args(args=args + ['fake_configfile.yml'])
    assert getattr(result, attrname) == expected_value


@pytest.mark.parametrize('args,attrname,expected_value', [
    ([], 'pull', False),
    (['--label', 'a=1', '--label', 'b=2'], 'label', ['a=1', 'b=2']),
    (['--pull'], 'pull', True),
    (['-t', 't1', '-t', 't2'], 'tag', ['t1', 't2']),
])
def test_docker_parse_args(args, attrname, expected_value):
    """Verify parsing of the Docker command line args"""
    result = parse_args(args=args + ['fake_configfile.yml'])
    assert getattr(result, attrname) == expected_value


@pytest.mark.parametrize('have_image,always_pull,expect_pull', [
    (False, False, True),
    (True, False, False),
    (True, True, True),
])
def test_pull_base_image(have_image, always_pull, expect_pull,
        mock_docker_client):
    image_name = 'junkapotamus:1.0'
    config = {'always_pull': always_pull, 'docker': {'base_image': image_name}}
    mock_docker_client.images.return_value = [{'Id': 'abc'}] if have_image \
        else []
    mock_docker_client.pull.return_value = '{"status": "great"}'

    pull_base_image(config, mock_docker_client)

    if expect_pull:
        mock_docker_client.pull.assert_called_with(repository='junkapotamus',
            tag='1.0')
    else:
        mock_docker_client.pull.assert_not_called()


def test_make_container(mock_docker_client):
    image_name = 'junkapotamus:1.0'
    container_id = 'abcd'
    config = {'docker': {'base_image': image_name}}

    mock_docker_client.create_container.return_value = {
        'Id': container_id,
        'Warnings': None,
    }

    assert make_container(config, mock_docker_client) == container_id
    mock_docker_client.create_container.assert_called_with(image_name,
        command='sleep 360000')
    mock_docker_client.start.assert_called_with(resource_id=container_id)


def test_run_command_list(mock_docker_client):
    fake_container_id = 'abcd'
    fake_exec_id = 'dumbledoor'
    commands = [['echo', 'hello']]

    # Set up the mocks
    mock_docker_client.exec_create.return_value = {'Id': fake_exec_id}
    mock_docker_client.exec_start.return_value = 'hello\n'
    mock_docker_client.exec_inspect.return_value = {'ExitCode': 0}

    # Run and verify the mocks were called properly
    run_command_list(commands, mock_docker_client, fake_container_id)
    mock_docker_client.exec_create.assert_called_with(
        container=fake_container_id, cmd=commands[0])
    mock_docker_client.exec_start.assert_called_with(exec_id=fake_exec_id)
    mock_docker_client.exec_inspect.assert_called_with(exec_id=fake_exec_id)


@pytest.mark.parametrize('docker_config,expected_extra_commands', [
    ({'cmd': ['ls', '-al']}, ['CMD ["ls", "-al"]']),
    ({'entrypoint': ['ls', '-al']}, ['ENTRYPOINT ["ls", "-al"]']),
    ({'expose_ports': [123, 456]}, ['EXPOSE 123', 'EXPOSE 456']),
    ({'volumes': ['/a', '/b']}, ['VOLUME /a', 'VOLUME /b']),
    ({'labels': {'name': 'foo'}}, ['LABEL "name"="foo"']),
    ({'labels': {'desc': 'f\\o"o'}}, ['LABEL "desc"="f\\\\o\\"o"']),
    ({'workdir': '/home'}, ['WORKDIR /home']),
    ({'env': {'PATH': '/bin'}}, ['ENV PATH /bin']),
    ({'env': {'VERSION': '\"foo 1.0\"'}}, ['ENV VERSION \"foo 1.0\"']),
])
def test_commit_image(docker_config, expected_extra_commands,
        mock_docker_client):
    config = {'docker': docker_config}
    container_id = 'fake_container_id'
    image_id = 'fake_image_id'

    mock_docker_client.commit.return_value = {'Id': image_id}

    assert commit_image(config, mock_docker_client, container_id) == image_id
    mock_docker_client.commit.assert_called_with(container_id,
        changes=expected_extra_commands)


def test_tag_image(mock_docker_client):
    config = {'docker': {'tags': ['foo:1.0', 'foo:latest']}}
    image_id = 'abcdzyxw'

    tag_image(config, mock_docker_client, image_id)
    mock_docker_client.remove_image.assert_has_calls([
        mock.call(resource_id='foo:1.0'),
        mock.call(resource_id='foo:latest'),
    ])
    mock_docker_client.tag.assert_has_calls([
        mock.call(resource_id=image_id, repository='foo', tag='1.0'),
        mock.call(resource_id=image_id, repository='foo', tag='latest'),
    ])


# vim:set ts=4 sw=4 expandtab:
