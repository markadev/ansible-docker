from __future__ import absolute_import, print_function, unicode_literals
import argparse
import docker
import logging
import os
import subprocess
import tempfile
from yaml.loader import SafeLoader

from ansible_docker.config import validate_config_type, ConfigurationError, \
    TYPE_STRING, TYPE_LIST_NUMBER, TYPE_LIST_STRING


logger = logging.getLogger('ansible-docker')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Building a Docker image with ansible')
    # TODO pass-thru to ansible
    #   -e, --vault-password-file
    #   -M --module-path
    #   --tags, --skip-tags
    #   -v
    # --pull
    # Override labels and identifiers
    #   -t,--tag
    #   --label
    # -q
    # --version
    parser.add_argument('configfile',
        help='Configuration file for building the container')
    return parser.parse_args()


def validate_docker_config(cfg):
    docker_cfg, docker_cfg_prefix = validate_config_type(cfg, 'docker',
        type=('map', dict), required=True)

    # Required parameters
    validate_config_type(docker_cfg, 'base_image', type=TYPE_STRING,
        prefix=docker_cfg_prefix, required=True)

    # Optional parameters
    validate_config_type(docker_cfg, 'build_volumes', type=TYPE_LIST_STRING,
        prefix=docker_cfg_prefix)
    validate_config_type(docker_cfg, 'cmd', type=TYPE_LIST_STRING,
        prefix=docker_cfg_prefix)
    validate_config_type(docker_cfg, 'entrypoint', type=TYPE_STRING,
        prefix=docker_cfg_prefix)
    validate_config_type(docker_cfg, 'expose_ports', type=TYPE_LIST_NUMBER,
        prefix=docker_cfg_prefix)
    validate_config_type(docker_cfg, 'labels', type=TYPE_LIST_STRING,
        prefix=docker_cfg_prefix)
    validate_config_type(docker_cfg, 'tags', type=TYPE_LIST_STRING,
        prefix=docker_cfg_prefix)
    validate_config_type(docker_cfg, 'volumes', type=TYPE_LIST_STRING,
        prefix=docker_cfg_prefix)
    validate_config_type(docker_cfg, 'workdir', type=TYPE_STRING,
        prefix=docker_cfg_prefix)


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
    validate_config_type(header, 'inventory_groups', type=TYPE_LIST_STRING)
    validate_docker_config(header)

    return (header, playbook_text)


def merge_command_line_args(args, config):
    """
    Merge the values specified on the command line into our configuration.
    """
    # TODO when command line args are defined
    pass


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


def run_ansible_playbook(config_file_name, config, playbook, container_name):
    # The playbook file should be in the same directory as the original
    # configuration file so that ansible will be able to find files
    # relative to the playbook.
    #inventory_fp, inventory_file_name = tempfile.mkstemp(
    #    prefix='tmpinventory-', suffix='.txt')
    playbook_file_name = os.path.join(os.path.dirname(config_file_name),
        ".tmp-{}".format(os.path.basename(config_file_name)))

    inventory_fp = None
    try:
        # Populate a temporary ansible inventory file
        inventory_fp = tempfile.NamedTemporaryFile(
            prefix='tmpinventory-', suffix='.txt')

        inventory_fp.write(container_name)
        inventory_fp.write(' ansible_connection=docker')
        inventory_fp.write(' ansible_python_interpreter="/usr/bin/env python"')
        inventory_fp.write('\n')
        # Add inventory groups
        for grp in set(config.get('inventory_groups', [])):
            inventory_fp.write("[{}]\n{}\n".format(grp, container_name))
        inventory_fp.flush()

        # Write the playbook to the temp file
        with open(playbook_file_name, 'w') as fp:
            fp.write(playbook)

        ansible_args = ['-i', inventory_fp.name]
        # TODO propagate through ansible command line args
        subprocess.check_call(['ansible-playbook'] + ansible_args +
            [playbook_file_name])
    except subprocess.CalledProcessError:
        raise RuntimeError("Ansible provisioning failed")
    finally:
        # Delete our temp files
        if inventory_fp is not None:
            inventory_fp.close()
        try:
            os.remove(playbook_file_name)
        except OSError:
            pass


def main():
    args = parse_args()
    try:
        config, playbook = load_configuration_file(args.configfile)
        merge_command_line_args(args, config)
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logger.error(e.message)
        raise SystemExit(2)

    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

    container_id = None
    try:
        logger.debug("Connecting to Docker daemon")
        docker_client = docker.Client()

        logger.info("Creating the container to provision")
        container_id = make_container(config, docker_client)
        container_info = docker_client.inspect_container(container_id)
        container_name = container_info['Name'].lstrip('/')
        logger.info("Created a container named %s", container_name)

        logger.info("Running the ansible playbook")
        run_ansible_playbook(args.configfile, config, playbook, container_name)

        logger.info("Committing the image")
        # TODO: construct this from the config values
        extra_commands = ['ENTRYPOINT /entrypoint.py']
        docker_client.commit(container_id, changes=extra_commands)
    except Exception as e:
        logger.error(e.message)
        raise SystemExit(3)
    finally:
        # Delete the container
        try:
            docker_client.remove_container(resource_id=container_id,
                force=True)
        except:
            pass


# vim:set ts=4 sw=4 expandtab:
