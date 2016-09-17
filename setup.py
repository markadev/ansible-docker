from setuptools import find_packages, setup


setup(
    name='ansible-docker',
    description='Build Docker images using ansible playbooks',
    author='Mark Aikens',
    author_email='markadev@primeletters.net',
    license='MIT',
    url='https://github.com/markadev/ansible-docker',

    packages=find_packages(),
    entry_points={
        'console_scripts': ['ansible-docker=ansible_image.docker:main'],
    },

    install_requires=[
        'ansible',
        'docker-py',
        'pyyaml',
        'six',
    ],

    tests_require=[
        'pytest',
    ],

    use_scm_version=True,
    setup_requires=['setuptools_scm', 'pytest-runner'],
)

# vim:set ts=4 sw=4 expandtab:
