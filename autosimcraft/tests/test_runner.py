# -*- coding: utf-8 -*-
"""
AutoSimcraft - tests for runner.py

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

from mock import patch, call
import pytest

import autosimcraft.runner
from fixtures import Container


def test_parse_argv():
    """ test parse_argv() """
    argv = ['-d', '-vv', '-c' 'foobar', '--genconfig']
    args = autosimcraft.runner.parse_args(argv)
    assert args.dry_run is True
    assert args.verbose == 2
    assert args.confdir == 'foobar'
    assert args.genconfig is True

def test_console_entry_genconfig():
    """ test console_entry_point() with --genconfig """
    with patch('autosimcraft.runner.parse_args') as mock_parse_args, \
         patch('autosimcraft.autosimcraft.AutoSimcraft.gen_config') as mock_gen_config:
        args = Container()
        setattr(args, 'genconfig', True)
        setattr(args, 'confdir', '/foo/bar')
        mock_parse_args.return_value = args
        with pytest.raises(SystemExit):
            autosimcraft.runner.console_entry_point()
    assert mock_parse_args.call_count == 1
    assert mock_gen_config.call_args_list == [call('/foo/bar')]

def test_console_entry():
    """ test console_entry_point() """
    with patch('autosimcraft.runner.parse_args') as mock_parse_args, \
         patch('autosimcraft.runner.AutoSimcraft', autospec=True) as mock_AS:
        args = Container()
        setattr(args, 'genconfig', False)
        setattr(args, 'confdir', '/foo/bar')
        setattr(args, 'dry_run', False)
        setattr(args, 'verbose', 1)
        mock_parse_args.return_value = args
        autosimcraft.runner.console_entry_point()
    assert mock_parse_args.call_count == 1
    assert mock_AS.mock_calls == [call(dry_run=False, verbose=1, confdir='/foo/bar'), call().run()]
    
