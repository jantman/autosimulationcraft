AutoSimulationCraft
========================

.. image:: https://pypip.in/v/autosimulationcraft/badge.png
   :target: https://crate.io/packages/autosimulationcraft

.. image:: https://pypip.in/d/autosimulationcraft/badge.png
   :target: https://crate.io/packages/autosimulationcraft

.. image:: https://landscape.io/github/jantman/autosimulationcraft/master/landscape.svg
   :target: https://landscape.io/github/jantman/autosimulationcraft/master
   :alt: Code Health

.. image:: https://secure.travis-ci.org/jantman/autosimulationcraft.png?branch=master
   :target: http://travis-ci.org/jantman/autosimulationcraft
   :alt: travis-ci for master branch

.. image:: https://codecov.io/github/jantman/autosimulationcraft/coverage.svg?branch=master
   :target: https://codecov.io/github/jantman/autosimulationcraft?branch=master
   :alt: coverage report for master branch

.. image:: http://www.repostatus.org/badges/0.1.0/active.svg
   :alt: Project Status: Active - The project has reached a stable, usable state and is being actively developed.
   :target: http://www.repostatus.org/#active

A python script to run `SimulationCraft <http://simulationcraft.org/>`_ reports for World of Warcraft characters when their gear/stats/level/etc. changes.

What It Does
-------------

When run, the script will first read in its configuration file (see below).

For each character in the ``CHARACTERS`` dictionary, it will use the BattleNet API
to request details about the character (currently: appearance, equipment, level,
stats and talents) and cache this information locally (in the same
directory as the configuration file). The first time a specific character is
found in the configuration file, a ``simc`` report will be generated for the
character, and emailed to a configurable (per-character) list of email addresses.

On subsequent runs, the script will compare BattleNet's current information for
the character with what the script saved to disk during its last run. If the
information is the same, that character will be skipped. Otherwise, a report
will be generated and sent via email (and also saved to disk).

This script is suitable for running via cron or another job scheduler (say, daily),
and it will automatically run SimulationCraft and email the report whenever
changes occur on the characters.

Status
-------

I got this working for myself originally as a single self-contained script.
The code - especially the tests - desperately need a refactor. If I keep using
it, or anyone else starts using it, maybe I'll try that.

Requirements
------------

* A working installation of `SimulationCraft <http://simulationcraft.org/>`_ with (at least) the command line portion.
* Python **2.7** - The upstream library that I chose to use for the BattleNet API only works with python2. As is the case
  with all of my current code, I target 2.7 through current (3.4) for development, as the effort to get code that also works with
  `horribly ancient <https://wiki.python.org/moin/Python2orPython3>`_ 2.6 isn't worth it. I've cut a branch to start work on solving
  this problem. Until then, 2.7 is it. Sorry.
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)

Installation
------------

It's recommended that you install into a virtual environment (virtualenv /
venv). See the `virtualenv usage documentation <http://www.virtualenv.org/en/latest/>`_
for information on how to create a venv. If you really want to install
system-wide, you can (using sudo).

.. code-block:: bash

    pip install autosimulationcraft

Configuration
-------------

Running

.. code-block:: bash

    autosimc --genconfig

Will generate a default configuration file at ``~/.autosimulationcraft/settings.py``. Open this with your
favorite text editor; the comments should be enough to help you configure it.

Usage
-----

I'd recommend calling ``autosimc`` from cron, or some other method of running it automatically
on a regular basis. If you want to, you *can* run it manually.

Bugs and Feature Requests
-------------------------

Bug reports and feature requests are happily accepted via the `GitHub Issue Tracker <https://github.com/jantman/autosimulationcraft/issues>`_. Pull requests are
welcome. Issues that don't have an accompanying pull request will be worked on
as my time and priority allows.

Development
===========

To install for development:

1. Fork the `autosimulationcraft <https://github.com/jantman/autosimulationcraft>`_ repository on GitHub
2. Create a new branch off of master in your fork.

.. code-block:: bash

    $ virtualenv autosimulationcraft
    $ cd autosimulationcraft && source bin/activate
    $ pip install -e git+git@github.com:YOURNAME/autosimulationcraft.git@BRANCHNAME#egg=autosimulationcraft
    $ cd src/autosimulationcraft

The git clone you're now in will probably be checked out to a specific commit,
so you may want to ``git checkout BRANCHNAME``.

Guidelines
----------

* pep8 compliant with some exceptions (see pytest.ini)
* 100% test coverage with pytest (with valid tests)

Testing
-------

Testing is done via `pytest <http://pytest.org/latest/>`_, driven by `tox <http://tox.testrun.org/>`_.

* testing is as simple as:

  * ``pip install tox``
  * ``tox``

* If you want to see code coverage: ``tox -e cov``

  * this produces two coverage reports - a summary on STDOUT and a full report in the ``htmlcov/`` directory

* If you want to pass additional arguments to pytest, add them to the tox command line after "--". i.e., for verbose pytext output on py27 tests: ``tox -e py27 -- -v``

Release Checklist
-----------------

1. Open an issue for the release; cut a branch off master for that issue.
2. Confirm that there are CHANGES.rst entries for all major changes.
3. Ensure that Travis tests passing in all environments.
4. Ensure that test coverage is no less than the last release (ideally, 100%).
5. Increment the version number in autosimulationcraft/version.py and add version and release date to CHANGES.rst, then push to GitHub.
6. Confirm that README.rst renders correctly on GitHub.
7. Upload package to testpypi, confirm that README.rst renders correctly.

   * Make sure your ~/.pypirc file is correct
   * ``python setup.py register -r https://testpypi.python.org/pypi``
   * ``python setup.py sdist bdist_wheel upload -r https://testpypi.python.org/pypi``
   * Check that the README renders at https://testpypi.python.org/pypi/autosimulationcraft

8. Create a pull request for the release to be merge into master. Upon successful Travis build, merge it.
9. Tag the release in Git, push tag to GitHub:

   * tag the release. for now the message is quite simple: ``git tag -a X.Y.Z -m 'X.Y.Z released YYYY-MM-DD'``
   * push the tag to GitHub: ``git push origin X.Y.Z``

10. Upload package to live pypi:

    * ``python setup.py sdist bdist_wheel upload``

11. make sure any GH issues fixed in the release were closed.
