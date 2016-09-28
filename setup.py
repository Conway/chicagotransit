from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='chicagotransit',
    version='0.4.0',
    description='A package for interfacing with Chicago Transit APIs',
    long_description=long_description,
    url='https://github.com/conway/ChicagoTransit',
    author='Jake Conway',
    author_email='jake.h.conway@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Natural Language :: English'
    ],
    keywords=['chicago', 'transit', 'wrapper', 'bus', 'train', 'cta', 'divvy', 'illinois', 'IL', 'transportation'],
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=requirements,
)