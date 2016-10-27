========
dockalot
========

*Building Docker images for the real world*

|build-status| |docs|

Introduction
============

``dockalot`` is a tool to build Docker images using Ansible playbooks for
application and configuration installation. It addresses several shortcomings
with the default Docker toolkit to make building non-trivial images easier.

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

``dockalot`` solves these problems by executing all of the installation
commands in one Docker layer. There are no hidden layers for credentials or
temporary files to hide in. You can focus on just installing software into
your Docker image using high-level Ansible modules and let the tools handle
the low-level details.


Features
========

- Build smaller images without having to think about Docker layers.
- Pass your API keys into the build process and don't worry about them
  getting stuck in any hidden Docker layers.
- Take advantage of purpose-built `Ansible modules
  <http://docs.ansible.com/ansible/list_of_files_modules.html>`_. Never
  run ``sed`` again!
- Use variables and templates in Ansible instead of clunky environment
  variables.
- Support for most of the important Dockerfile commands. Goal is to
  have feature-parity with Dockerfiles.


Installation
============

Requirements:
 * Python 2.7
 * Docker >= 1.12

Install ``dockalot`` using *pip*::

    ubuntu@ubuntu-vm:~$ sudo pip install dockalot

Or, to install without root access you can use a
`virtual environment <https://pypi.python.org/pypi/virtualenv>`_::

    ubuntu@ubuntu-vm:~$ mkvirtualenv dockalot
    ubuntu@ubuntu-vm:~$ . dockalot/bin/activate
    (dockalot) ubuntu@ubuntu-vm:~$ pip install dockalot


Example Usage
=============

A simple configuration file (``example1.yml``) to build an image looks like
this::

    ---
    docker:
      base_image: "python:2.7"
      entrypoint: [ "/entrypoint.py" ]
      tags:
        - myapp
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

Build the image::

    ubuntu@ubuntu-vm:~$ dockalot example1.yml 
    INFO:Creating the container to provision
    ...
    INFO:Committing the image
    INFO:Created sha256:662a2be8c1215de09fc410f2c5c7fb2e8b6ed00b125c4cd27fe8a28972f8542c
    INFO:Tagging image myapp:latest
    ubuntu@ubuntu-vm:~$

Then run your shiny new image::

    ubuntu@ubuntu-vm:~$ docker run myapp
    I'm a Python script
    Wheeeeee!!!!
    ubuntu@ubuntu-vm:~$

Also take a look at some more `complex examples
<https://github.com/markadev/dockalot/tree/master/examples>`_.


License
=======

The project is licensed under the MIT license.


.. |docs| image:: https://readthedocs.org/projects/dockalot/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: https://dockalot.readthedocs.io/en/latest/?badge=latest

.. |build-status| image:: https://travis-ci.org/markadev/dockalot.svg?branch=master
    :alt: build status
    :target: https://travis-ci.org/markadev/dockalot
