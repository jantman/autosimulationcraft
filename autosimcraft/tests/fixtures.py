# -*- coding: utf-8 -*-
"""
AutoSimcraft - fixtures for AutoSimcraft

The latest version of this package is available at:
<https://github.com/jantman/autosimcraft>

##################################################################################
Copyright 2015 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of autosimcraft.

    autosimcraft is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    autosimcraft is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with autosimcraft.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
##################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/autosimcraft> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
##################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

"""

import pytest
from mock import MagicMock, call, patch, Mock, mock_open
import battlenet
import logging
from contextlib import nested
from autosimcraft import autosimcraft


class Container:
    pass


@pytest.fixture
def mock_ns():
    """ a mocked AutoSimcraft object """
    bn = MagicMock(spec_set=battlenet.Connection)
    conn = MagicMock(spec_set=battlenet.Connection)
    bn.return_value = conn
    rc = Mock()
    lc = Mock()
    wc = Mock()
    mocklog = MagicMock(spec_set=logging.Logger)
    def mock_ap_se(p):
        return p
    def mock_eu_se(p):
        return p.replace('~/', '/home/user/')
    with nested(
            patch('autosimcraft.autosimcraft.battlenet.Connection', bn),
            patch('autosimcraft.autosimcraft.AutoSimcraft.read_config', rc),
            patch('autosimcraft.autosimcraft.AutoSimcraft.load_character_cache', lc),
            patch('autosimcraft.autosimcraft.os.path.expanduser'),
            patch('autosimcraft.autosimcraft.os.path.abspath'),
    ) as (bnp, rcp, lcc, mock_eu, mock_ap):
        mock_ap.side_effect = mock_ap_se
        mock_eu.side_effect = mock_eu_se
        s = autosimcraft.AutoSimcraft(verbose=2, logger=mocklog)
    return (bn, rc, mocklog, s, conn, lcc)

@pytest.fixture
def mock_bnet_character(bnet_data):
    char = battlenet.things.Character(battlenet.UNITED_STATES,
                                      realm='Area 52',
                                      name='jantman',
                                      data=bnet_data)
    return char
