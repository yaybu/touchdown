from setuptools import find_packages, setup

version = '0.15.16'

setup(
    name='touchdown',
    version=version,
    url='http://yaybu.com/',
    description='Orchestration and configuration management in Python',
    long_description=open('README.rst').read(),
    author='Isotoma Limited',
    author_email='support@isotoma.com',
    license='Apache Software License',
    classifiers=[
        'Intended Audience :: System Administrators',
        'Operating System :: POSIX',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'six',
        'contextlib2',
        'netaddr',
        'fuselage>=1.0.0',
        'botocore>=1.4.28',
        'requests',
        'python-gnupg',
    ],
    entry_points='''
        [console_scripts]
        touchdown = touchdown.core.main:main
    ''',
)
