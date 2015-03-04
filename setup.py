from setuptools import setup
from sys import version_info
from autosimulationcraft.version import VERSION

if version_info[0] > 2 or version_info[1] < 7:
    raise SystemExit("ERROR - autosimulationcraft currently only works with python 2.7; this should be fixed soon.")

with open('README.rst') as file:
    long_description = file.read()

requires = [
    'battlenet>=0.2.6',
    'dictdiffer>=0.3.0',
]

classifiers = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2 :: Only',
    'Programming Language :: Python :: 2.7',
    'Topic :: Games/Entertainment',
]

setup(
    name='autosimulationcraft',
    version=VERSION,
    author='Jason Antman',
    author_email='jason@jasonantman.com',
    packages=['autosimulationcraft', 'autosimulationcraft.tests'],
    entry_points="""
    [console_scripts]
    autosimc = autosimulationcraft.runner:console_entry_point
    """,
    url='http://github.com/jantman/AutoSimulationCraft/',
    description='A python script to run SimulationCraft reports for World of Warcraft characters when their gear/stats/level/etc. changes.',
    long_description=long_description,
    install_requires=requires,
    keywords="WoW Warcraft simc SimulationCraft",
    classifiers=classifiers
)
