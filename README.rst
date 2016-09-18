===============
ansible-docker
===============
*Building Docker images for the real world.*

``ansible-docker`` is a tool to help building Docker images using Ansible
playbooks as the provisioning language. It addresses several shortcomings
with the default Docker toolkit to make building non-trivial images much
more practical.

Using Dockerfiles is fine if you are repackaging an open source or other
publicly available package. But if you aren't, you might have one or more
of these problems:
 * Building your image requires credentials to a private source code or
   package repository
 * Building your image requires a custom package installation procedure more
   complicated than ``apt-get install``

Because of the way ``docker build`` works by building your image in layers
on top of layers, you may find that your super-secret private repository
credentials gets trapped in one of those layers. Temporary files part of
any non-trivial package installation also get trapped in those layers
causing your final Docker image to be much larger than they need to be.


Example Use
===========

Requirements:
 * Docker >= 1.12

Try it out with one of the examples that comes with the source code::

   ansible-docker examples/mysql/mysql-5.7.yml


Configuration File
==================
The configuration file for ``ansible-docker`` is a single YAML file
containing 2 sections separated by ``---``. The first section contains
the configuration for the Docker image to build. The second section is
a full-blown Ansible playbook that you can make as simple or as complex
as you need.  

A simple configuration file::

    ---
    docker:
      base_image: "python:2.7-slim"
      entrypoint: [ "/entrypoint.py" ]
    ---
    - name: Provision the container
      gather_facts: no
      hosts: all
      tasks:
        - name: Install the thing
          copy: 
            dest: /entrypoint.py
            content: |
              #!/usr/bin/env python
              print("I'm a Python script")
              print("Wheeeeee!!!!")
            mode: 0755

Also check out the ``examples`` directory for more examples!
