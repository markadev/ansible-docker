from __future__ import absolute_import, print_function, unicode_literals
import argparse
import docker
import json
import logging
import os
import pkg_resources
import six
import subprocess
import tempfile
from yaml.loader import SafeLoader

from dockalot.config import ArgSaverAction, Config, ConfigurationError
from dockalot.file_util import safe_delete


logger = logging.getLogger('dockalot')


def split_repo_tag(repotag):
    # Tag defaults to 'latest' if no tag is specified
    try:
        repository, tag = repotag.split(':', 1)
    except ValueError:
        repository = repotag
        tag = 'latest'
    return (repository, tag)


def escape_quotes(s):
    """
    Returns a string with backslash and double-quote characters escaped.
    """
    return s.replace('\\', '\\\\').replace('"', '\\"')


def parse_args(args=None):
    try:
        version = pkg_resources.get_distribution('dockalot').version
    except pkg_resources.DistributionNotFound:
        version = 'version unknown'

    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('--ask-vault-pass',
        action=ArgSaverAction, nargs=0, dest='ansible_args',
        help='Prompt for the password to decrypt Ansible vaults')
    base_parser.add_argument('-e',
        action=ArgSaverAction, dest='ansible_args', metavar='EXTRA_VAR',
        help='Set additional Ansible variables as key=value')
    base_parser.add_argument('--keep-on-failure', action='store_true',
        help='Do not delete the Docker container used to build the image if '
            'the build fails. This allows manual inspection of the container '
            'to help debug build configurations.')
    base_parser.add_argument('--vault-password-file',
        action=ArgSaverAction, dest='ansible_args', metavar='FILE',
        help='Specify a file with the password to decrypt an Ansible vault')
    base_parser.add_argument('--version',
        action='version', version='%(prog)s {}'.format(version))
    base_parser.add_argument('configfile',
        help='Configuration file describing how to build the image')

    parser = argparse.ArgumentParser(
        parents=[base_parser],
        description='Build a Docker image with ansible')

    parser.add_argument('--label', action='append',
        help='Add a label to the image of the format name=value. This ' +
             'option can be specified multiple times to add multiple labels.')
    parser.add_argument('--pull', action='store_true',
        help='Always pull down the latest base image')
    parser.add_argument('-t', dest='tag', action='append',
        help='A name and optional tag (in the name:tag) format. This option ' +
             'can be specified multiple times to apply multiple tags.')

    # TODO pass-thru to ansible
    #   -M --module-path
    #   -v
    return parser.parse_args(args)


def load_configuration_file(filename):
    """
    Opens the configuration file and parsers the first YAML document.
    The first document is the configuration header where our configuration
    is defined. Our configuration is validated before being returned.

    The remaining part of the YAML file is read verbatim and returned as a
    string so it can be passed untouched to the next stage (ansible).

    :returns: A tuple (dict, str) containing the dictionary of our
              configuration and a string of the remaining text in the
              configuration file.
    """
    with open(filename) as fp:
        loader = SafeLoader(fp)
        header = loader.get_data()
        if not loader.check_data():
            raise ConfigurationError("No ansible playbook defined in {}"
                .format(filename))

        # The yaml library stripped out the leading '---' so we add it back.
        playbook_text = "---"

        # yaml library signifies end of file with a NUL character so we
        # check for that.
        while playbook_text[-1] != '\0':
            text = loader.prefix(1024)
            playbook_text += text
            loader.forward(len(text))
        playbook_text = playbook_text.rstrip('\0')

    # Validate our stuff
    config = Config(header)
    return (config, playbook_text)


def pull_base_image(config, docker_client):
    """
    Pulls the base image if it's not already present. If the option to always
    pull is set then this always pulls down the latest image.
    """
    repository, tag = split_repo_tag(config['docker']['base_image'])

    if not config['always_pull']:
        # Check if we already have the base image
        images = docker_client.images(name="{}:{}".format(repository, tag))
        if len(images) > 0:
            # We already have the image
            return

    # Either we don't have the image or we were configured to always pull it
    logger.info("Pulling image %s:%s", repository, tag)
    result = docker_client.pull(repository=repository, tag=tag) \
        .rstrip().split('\n')
    final_result = json.loads(result[-1])
    if 'error' in final_result:
        raise RuntimeError(final_result['error'])
    if 'status' in final_result:
        logger.info(final_result['status'])


def make_container(config, docker_client):
    """
    Creates and starts the container that ansible will run against.
    """
    container = docker_client.create_container(
        config['docker']['base_image'],
        command='sleep 360000')

    if container['Warnings'] is not None:
        # I have never seen this set but display it anyway
        logger.warn(container['Warnings'])

    container_id = container['Id']
    logger.debug("Created container, id=%s", container_id)

    docker_client.start(resource_id=container_id)
    logger.debug("Started container")

    return container_id


def docker_exec(docker_client, container_id, command):
    logger.debug("Executing \"%s\"", command)

    result = docker_client.exec_create(container=container_id, cmd=command)
    exec_id = result['Id']
    exec_output = docker_client.exec_start(exec_id=exec_id).split('\n')
    exec_info = docker_client.exec_inspect(exec_id=exec_id)
    return (exec_info['ExitCode'], exec_output)


def run_command_list(commands, docker_client, container_id):
    """
    Runs a list of commands in the container
    """
    for command in commands:
        logger.info("Running \"%s\"", command)
        rc, output = docker_exec(docker_client, container_id, command)
        log_level = logging.INFO if rc == 0 else logging.ERROR
        for line in output:
            logger.log(log_level, line.rstrip())
        if rc != 0:
            raise RuntimeError('command failed')


def run_ansible_playbook(config_file_name, config, playbook, container_name):
    # The playbook file should be in the same directory as the original
    # configuration file so that ansible will be able to find files
    # relative to the playbook.
    tmp_playbook_file_name = os.path.join(os.path.dirname(config_file_name),
        ".tmp-{}".format(os.path.basename(config_file_name)))

    inventory_fp = None
    try:
        # Populate a temporary ansible inventory file
        inventory_fp = tempfile.NamedTemporaryFile(
            prefix='tmpinventory-', suffix='.txt')

        inventory_fp.write(container_name)
        inventory_fp.write(' ansible_connection=docker')
        inventory_fp.write('\n')
        # Add inventory groups
        for grp in set(config.get('inventory_groups', [])):
            inventory_fp.write("[{}]\n{}\n".format(grp, container_name))
        inventory_fp.flush()

        # Write the playbook to the temp file
        with open(tmp_playbook_file_name, 'w') as fp:
            fp.write(playbook)

        ansible_args = ['-i', inventory_fp.name] + \
            config.get('ansible_args', [])
        subprocess.check_call(['ansible-playbook'] + ansible_args +
            [tmp_playbook_file_name])
    except subprocess.CalledProcessError:
        raise RuntimeError("Ansible provisioning failed")
    finally:
        # Delete our temp files
        if inventory_fp is not None:
            inventory_fp.close()
        safe_delete(tmp_playbook_file_name)

        # Delete the .retry file if one was created
        safe_delete(os.path.splitext(tmp_playbook_file_name)[0] + '.retry')


def commit_image(config, docker_client, container_id):
    dcfg = config['docker']
    extra_commands = []

    if 'cmd' in dcfg:
        extra_commands.append("CMD {}".format(json.dumps(dcfg['cmd'])))
    if 'entrypoint' in dcfg:
        extra_commands.append("ENTRYPOINT {}".format(
            json.dumps(dcfg['entrypoint'])))
    for port in dcfg.get('expose_ports', []):
        extra_commands.append("EXPOSE {}".format(port))
    for volume in dcfg.get('volumes', []):
        extra_commands.append("VOLUME {}".format(volume))
    for k, v in six.iteritems(dcfg.get('labels', {})):
        extra_commands.append("LABEL \"{}\"=\"{}\"".format(
            escape_quotes(k), escape_quotes(str(v))))
    if 'workdir' in dcfg:
        extra_commands.append("WORKDIR {}".format(dcfg['workdir']))
    for k, v in six.iteritems(dcfg.get('env', {})):
        # No value quoting is necessary with this form of the ENV command
        extra_commands.append("ENV {} {}".format(k, v))

    image = docker_client.commit(container_id, changes=extra_commands)
    return image['Id']


def tag_image(config, docker_client, image_id):
    repotags = config['docker'].get('tags', [])
    for repotag in repotags:
        repo, tag = split_repo_tag(repotag)
        logger.info("Tagging image %s:%s", repo, tag)

        # Remove any existing tag first. This prevents anonymous images
        # from accumulating if a tag (like 'latest') is reused
        try:
            docker_client.remove_image(resource_id=repotag)
        except docker.errors.APIError:
            # Either tag was not found or it couldn't be removed because
            # it's in use. The 'tag' command will still succed in the
            # latter case.
            pass

        docker_client.tag(resource_id=image_id, repository=repo, tag=tag)


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

    args = parse_args()
    try:
        config, playbook = load_configuration_file(args.configfile)
        config.merge_command_line_args(args)
    except IOError as e:
        logger.error(e.strerror)
        raise SystemExit(2)
    except Exception as e:
        logger.error(e.message)
        raise SystemExit(2)

    container_id = None
    keep_container = args.keep_on_failure
    try:
        logger.debug("Connecting to Docker daemon")
        docker_client = docker.from_env()

        pull_base_image(config, docker_client)

        logger.info("Creating the container to provision")
        container_id = make_container(config, docker_client)
        container_info = docker_client.inspect_container(container_id)
        container_name = container_info['Name'].lstrip('/')
        logger.info("Created a container named %s", container_name)

        logger.info("Preparing the container")
        run_command_list(config.get('preparation_commands', []),
            docker_client, container_id)

        logger.info("Running the ansible playbook")
        run_ansible_playbook(args.configfile, config, playbook, container_name)

        logger.info("Cleaning up the container")
        run_command_list(config.get('cleanup_commands', []),
            docker_client, container_id)

        logger.info("Committing the image")
        image_id = commit_image(config, docker_client, container_id)
        logger.info("Created %s", image_id)

        # Never keep the container once the build is successful
        keep_container = False

        tag_image(config, docker_client, image_id)
    except KeyboardInterrupt as e:
        logger.error("Interrupted...")
        raise SystemExit(16)
    except Exception as e:
        logger.error(e.message)
        raise SystemExit(3)
    finally:
        # Delete the container
        try:
            if not keep_container and container_id is not None:
                docker_client.remove_container(resource_id=container_id,
                    force=True)
        except:
            pass


# vim:set ts=4 sw=4 expandtab:
