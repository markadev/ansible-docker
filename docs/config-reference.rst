============================
Configuration File Reference
============================

Dockalot builds Docker images based on a configuration file. The configuration
file uses standard YAML_ syntax and contains two YAML sections, each one
starting with a ``---``.

The first section is a configuration header with metadata for the image to
build, including everything normally set in a Dockerfile such as:

 * the base image to start from
 * exposed ports
 * entrypoint and command
 * volumes
 * etc.

The second section contains an `Ansible playbook`_ which is a sequence of
commands to excecute to install and modify files within the Docker image.

Some configuration can also be specified with command line options. When
something is specified on both the command line and in the configuration
file then the command line options take precedence.

::

    ---
    CONFIGURATION HEADER
    ---
    ANSIBLE PLAYBOOK


Configuration Header
====================

The Dockalot configuration header lets you configure the metadata for
building the Docker image. 

``docker``
----------
:Under: top-level
:Description:
    A key/value map for Docker image related metadata


``entrypoint``
~~~~~~~~~~~~~~
:Under: ``docker``
:Value type: List of strings
:Description:
    Set the entrypoint for the image. The value should be a list of strings
    where the first is the executable name and the remaining strings are
    arguments for the executable.
:See also: https://docs.docker.com/engine/reference/builder/#exec-form-entrypoint-example

**Example**::

    docker:
      entrypoint: ['executable', 'arg1', 'arg2']


``env``
~~~~~~~
:Under: ``docker``
:Value type: Map of strings
:Description:
    A key/value map of environment variables to create in the final image.
    This should be a map of environment variable name to value. Values can
    contain spaces.

    The environment variable is not created until *after* the image has
    been built. Consequently, the environment variables defined here cannot
    be used within the Ansible playbook.

**Example**::

    docker:
      env:
        DATADIR: /var/lib/db
        MY_VERSION: "4.5"


``cmd``
~~~~~~~
:Under: ``docker``
:Value type: List of strings
:Description:
    Sets the command for the image. The value should be a list of string.

    When no entrypoint is defined for the image then this list will be the
    executable and arguments to execute. 

    When an entrypoint is also defined then this list will be passed to the
    entrypoint as arguments.
:See also: https://docs.docker.com/engine/reference/builder/#cmd

**Example**::

    docker:
      cmd: [ '/startit.sh', '-m', 'dev' ]


``expose_ports``
~~~~~~~~~~~~~~~~
:Under: ``docker``
:Value type: List of integers
:Description:
    Sets the ports that the image exposes.

**Example**::

    docker:
      expose_ports: [ 80, 443 ]

OR::

    docker:
      expose_ports:
        - 80
        - 443


``labels``
~~~~~~~~~~
:Under: ``docker``
:Value type: Map of strings
:Description:
    A key/value map of labels to add to the final image.

**Example**::

    docker:
      labels:
        description: "Description of my image"
        net.primeletters.version: "1.0"


``tags``
~~~~~~~~
:Under: ``docker``
:Value type: List of strings
:Description:
    A list of tags to apply to the final image, in the form of ``image:tag``.
    If ``tag`` is omitted then the default value of ``latest`` will be used.

**Example**::

    docker:
      tags: [ 'myapp', 'myapp:1.0' ]

OR::

    docker:
      tags:
        - myapp
        - myapp:1.0


``volumes``
~~~~~~~~~~~
:Under: ``docker``
:Value type: List of strings
:Description:
    A list of directories within the image that are volume mount points.
:See also: https://docs.docker.com/engine/reference/builder/#volume

**Example**::

    docker:
      volumes:
        - /var/log
        - /data


``workdir``
~~~~~~~~~~~
:Under: ``docker``
:Value type: String
:Description:
    The working directory within the image. This is the working directory that
    containers created using the image will start out executing in.

**Example**::

    docker:
      workdir: /app



``inventory_groups``
--------------------
:Under: top-level
:Value type: List of strings
:Description:
    This is a list of extra ansible groups to add the builder container to.
    You will usually never need to use this option.



.. _`Ansible playbook`: http://docs.ansible.com/ansible/playbooks.html
.. _YAML: https://learnxinyminutes.com/docs/yaml/
