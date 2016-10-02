===============
dockalot
===============
*Building Docker images for the real world.*

``dockalot`` is a tool to help building Docker images using Ansible
playbooks as the provisioning language. It addresses several shortcomings
with the default Docker toolkit to make building non-trivial images much
more practical.

Using a Dockerfile is fine if you are repackaging an open source or other
publicly available package. But if you aren't, you might have one or more
of these problems:

* Building your image requires credentials to a private source code or
  package repository
* Building your image requires a custom package installation procedure more
  complicated than ``apt-get install``

Because of the way ``docker build`` works by building your image in layers
on top of layers, you may find that your super-secret private repository
credentials gets trapped in one of those layers. Go ahead, export an image
using ``docker save`` and poke around the layers of an image you've already
built. Is that *your* access token in there? Well, it's everyone's access
token now...

Temporary files part of any non-trivial package installation also get
trapped in those middle layers causing your final Docker image to be much
larger than they need to be. Workarounds for this problem include ``&&``-itis;
joining dozens of shell commands together with ``&&`` in an attempt to keep
them all on the same layer. When you do this you lose the ability to add
comments in-line and your Dockerfile becomes a mess.

It doesn't have to be this way.

``dockalot`` solves these problems by executing all of the provisioning
in one Docker layer. There are no hidden layers for credentials or temporary
files to hide in. You can focus on just installing software into your Docker
image and let the tools handle the rest.


Example Use
===========

Requirements:
 * Docker >= 1.12

Try it out with one of the examples that comes with the source code::

   dockalot examples/mysql/mysql-5.7.yml


Configuration File
==================
The configuration file for ``dockalot`` is a single YAML file
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
