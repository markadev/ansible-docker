#!/bin/sh

ansible-playbook -i localhost, -e "ansible_python_interpreter=\"/usr/bin/env python\"" test.yml
