from setuptools import find_packages, setup


setup(
    name='dockalot',
    description=('Build Docker images for the real world '
        'using ansible playbooks'),
    author='Mark Aikens',
    author_email='markadev@primeletters.net',
    license='MIT',
    url='https://github.com/markadev/dockalot',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: System :: Installation/Setup',
        'Topic :: Utilities',
    ],

    packages=find_packages(),
    entry_points={
        'console_scripts': ['dockalot=dockalot.docker:main'],
    },

    install_requires=[
        'ansible>=2.1',
        'docker-py',
        'pyyaml',
        'six',
    ],

    tests_require=[
        'docker-py',
        'mock~=2.0',
        'pytest~=3.0',
    ],

    use_scm_version=True,
    setup_requires=['setuptools_scm', 'pytest-runner'],
)

# vim:set ts=4 sw=4 expandtab:
