# -*- coding: utf-8 -*-
"""
AutoSimulationCraft - tests for runner.py

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

import re

import autosimulationcraft.version


# from: <https://github.com/mojombo/semver.org/issues/59#issuecomment-57884619>
semver_re = re.compile(r'^((?:0|(?:[1-9]\d*)))\.((?:0|(?:[1-9]\d*)))\.'
                       '((?:0|(?:[1-9]\d*)))(?:-([0-9A-Za-z-]+(\.[0-9A-Za-z-]+)'
                       '*))?(?:\+([0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*))?$')


def test_version():
    assert semver_re.match(autosimulationcraft.version.VERSION) is not None
