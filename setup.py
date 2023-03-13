from pathlib import Path

from pkg_resources import parse_requirements
from setuptools import setup, find_packages

import polyfile

setup(
    name='polyfile',
    version=polyfile.__version__,
    python_requires='>=3.8.0',
    packages=find_packages('.'),
    long_description=Path('README.md').open('r').read(),
    long_description_content_type='text/markdown',
    install_requires=list(map(str, parse_requirements(Path('requirements.txt').open('r')))),
    include_package_data=True,
)
