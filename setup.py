from setuptools import setup, find_packages
from pip.req import parse_requirements

__version__ = None
with open('flyby/__init__.py') as f:
    exec(f.read())

setup(
    name='flyby',
    version=__version__,
    packages=find_packages(),
    package_data={'flyby': ['config/*.j2']},
    entry_points='''
        [console_scripts]
        flyby=flyby.cli:cli
    ''',
    install_requires=[str(ir.req) for ir in parse_requirements('requirements.txt', session=False)]
)
