# -*- coding: utf-8 -*-
"""
AutoSimulationCraft

The latest version of this package is available at:
<https://github.com/jantman/autosimulationcraft>

##################################################################################
Copyright 2015 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of autosimulationcraft.

    autosimulationcraft is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    autosimulationcraft is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with autosimulationcraft.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
##################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/autosimulationcraft> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
##################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

"""

import sys
import argparse
import os

from config import DEFAULT_CONFDIR
from version import VERSION
from autosimulationcraft import AutoSimulationCraft


def parse_args(argv):
    """
    parse arguments/options

    this uses the new argparse module instead of optparse
    see: <https://docs.python.org/2/library/argparse.html>
    """
    p = argparse.ArgumentParser(description='A python script to run SimulationCraft '
                                'reports for World of Warcraft characters when their '
                                'gear/stats/level/etc. changes.')
    p.add_argument('-d', '--dry-run', dest='dry_run', action='store_true', default=False,
                   help="dry-run - don't send email, just say what would be sent")
    p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-c', '--configdir', dest='confdir', action='store',
                   type=str, default=DEFAULT_CONFDIR,
                   help='configuration directory (default: {c})'.format(c=DEFAULT_CONFDIR))
    p.add_argument('-s', '--no-stat', dest='no_stat', action='store_true', default=False,
                   help='ignore overall stats when determining if character changed')
    p.add_argument('--genconfig', dest='genconfig', action='store_true', default=False,
                   help='generate a sample configuration file at configdir/settings.py')
    p.add_argument('--version', dest='version', action='store_true', default=False,
                   help='print version number and exit.')
    args = p.parse_args(argv)

    return args


def console_entry_point():
    args = parse_args(sys.argv[1:])
    if args.version:
        print(VERSION)
        raise SystemExit()
    if args.genconfig:
        AutoSimulationCraft.gen_config(args.confdir)
        cpath = os.path.join(os.path.abspath(os.path.expanduser(args.confdir)), 'settings.py')
        print("Configuration file generated at: {c}".format(c=cpath))
        raise SystemExit()
    script = AutoSimulationCraft(dry_run=args.dry_run, verbose=args.verbose, confdir=args.confdir)
    script.run(no_stat=args.no_stat)


if __name__ == "__main__":
    console_entry_point()
