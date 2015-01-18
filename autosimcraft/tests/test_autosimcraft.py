# -*- coding: utf-8 -*-
"""
AutoSimcraft - tests for AutoSimcraft class

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
import logging
from mock import MagicMock, call, patch, Mock, mock_open
from contextlib import nested
import sys
import datetime
from copy import deepcopy
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from base64 import b64decode

from freezegun import freeze_time
import battlenet

from autosimcraft import autosimcraft
from data_fixtures import *
from fixtures import *



def test_default_confdir():
    assert autosimcraft.DEFAULT_CONFDIR == '~/.autosimcraft'


class Test_AutoSimcraft:

    def test_init_default(self):
        """ test SimpleScript.init() """
        bn = MagicMock(spec_set=battlenet.Connection)
        rc = Mock()
        with nested(
                patch('autosimcraft.autosimcraft.battlenet.Connection', bn),
                patch('autosimcraft.autosimcraft.AutoSimcraft.read_config', rc)
        ):
            s = autosimcraft.AutoSimcraft(dry_run=False,
                                                 verbose=0,
                                                 confdir='~/.autosimcraft'
                                             )
        assert bn.mock_calls == [call()]
        assert rc.call_args_list == [call('~/.autosimcraft')]
        assert s.dry_run is False
        assert type(s.logger) == logging.Logger
        assert s.logger.level == logging.NOTSET

    def test_init_logger(self):
        """ test SimpleScript.init() with specified logger """
        m = MagicMock(spec_set=logging.Logger)
        bn = MagicMock(spec_set=battlenet.Connection)
        rc = Mock()
        with nested(
                patch('autosimcraft.autosimcraft.battlenet.Connection', bn),
                patch('autosimcraft.autosimcraft.AutoSimcraft.read_config', rc)
        ):
            s = autosimcraft.AutoSimcraft(logger=m)
        assert s.logger == m

    def test_init_dry_run(self):
        """ test SimpleScript.init() with dry_run=True """
        bn = MagicMock(spec_set=battlenet.Connection)
        rc = Mock()
        with nested(
                patch('autosimcraft.autosimcraft.battlenet.Connection', bn),
                patch('autosimcraft.autosimcraft.AutoSimcraft.read_config', rc)
        ):
            s = autosimcraft.AutoSimcraft(dry_run=True)
        assert s.dry_run is True

    def test_init_verbose(self):
        """ test SimpleScript.init() with verbose=1 """
        bn = MagicMock(spec_set=battlenet.Connection)
        rc = Mock()
        with nested(
                patch('autosimcraft.autosimcraft.battlenet.Connection', bn),
                patch('autosimcraft.autosimcraft.AutoSimcraft.read_config', rc)
        ):
            s = autosimcraft.AutoSimcraft(verbose=1)
        assert s.logger.level == logging.INFO

    def test_init_debug(self):
        """ test SimpleScript.init() with verbose=2 """
        bn = MagicMock(spec_set=battlenet.Connection)
        rc = Mock()
        with nested(
                patch('autosimcraft.autosimcraft.battlenet.Connection', bn),
                patch('autosimcraft.autosimcraft.AutoSimcraft.read_config', rc)
        ):
            s = autosimcraft.AutoSimcraft(verbose=2)
        assert s.logger.level == logging.DEBUG

    def test_read_config_missing(self, mock_ns):
        """ test read_config() when settings file is missing """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        with nested(
                patch('autosimcraft.autosimcraft.os.path.exists'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.import_from_path'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.validate_config'),
        ) as (mock_path_exists, mock_import, mock_validate):
            mock_path_exists.return_value = False
            with pytest.raises(SystemExit) as excinfo:
                s.read_config('/foo')
            assert excinfo.value.code == 1
        assert call('Reading configuration from: /foo/settings.py') in mocklog.debug.call_args_list
        assert mock_import.call_count == 0
        assert mock_path_exists.call_count == 1
        assert mocklog.error.call_args_list == [call("ERROR - configuration file does not exist. Please run with --genconfig to generate an example one.")]

    def test_read_config(self, mock_ns):
        """ test read_config() working correctly """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        mock_settings = Container()
        setattr(mock_settings, 'CHARACTERS', [])
        setattr(mock_settings, 'DEFAULT_SIMC', 'foo')
        setattr(s, 'settings', mock_settings)
        with nested(
                patch('autosimcraft.autosimcraft.os.path.exists'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.import_from_path'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.validate_config'),
        ) as (mock_path_exists, mock_import, mock_validate):
            mock_path_exists.return_value = True
            s.read_config('/foo')
        assert call('Reading configuration from: /foo/settings.py') in mocklog.debug.call_args_list
        assert mock_import.call_args_list == [call('/foo/settings.py')]
        assert mock_path_exists.call_count == 1
        assert mock_validate.call_args_list == [call()]
        
    def test_genconfig(self):
        """ test gen_config() """
        cd = '/foo'
        with nested(
                patch('autosimcraft.autosimcraft.os.path.exists'),
                patch('autosimcraft.autosimcraft.open', create=True)
        ) as (mock_pe, mock_open):
            mock_open.return_value = MagicMock(spec=file)
            mock_pe.return_value = True
            autosimcraft.AutoSimcraft.gen_config(cd)
        file_handle = mock_open.return_value.__enter__.return_value
        assert mock_open.call_args_list == [call('/foo/settings.py', 'w')]
        assert file_handle.write.call_count == 1

    def test_genconfig_nodir(self):
        """ test gen_config() with config directory missing """
        cd = '/foo'
        with nested(
                patch('autosimcraft.autosimcraft.os.path.exists'),
                patch('autosimcraft.autosimcraft.os.mkdir'),
                patch('autosimcraft.autosimcraft.open', create=True)
        ) as (mock_pe, mock_mkdir, mock_open):
            mock_open.return_value = MagicMock(spec=file)
            mock_pe.return_value = False
            autosimcraft.AutoSimcraft.gen_config(cd)
        file_handle = mock_open.return_value.__enter__.return_value
        assert mock_open.call_args_list == [call('/foo/settings.py', 'w')]
        assert file_handle.write.call_count == 1
        assert mock_mkdir.call_args_list == [call('/foo')]

    def test_validate_config_no_characters(self, mock_ns):
        """ test validate_config() with no characters """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        mock_settings = Container()
        setattr(mock_settings, 'DEFAULT_SIMC', 'foo')
        setattr(s, 'settings', mock_settings)
        with pytest.raises(SystemExit) as excinfo:
            res = s.validate_config()
        assert excinfo.value.code == 1
        assert mocklog.error.call_args_list == [call("ERROR: Settings file must define CHARACTERS list")]

    def test_validate_config_characters_not_list(self, mock_ns):
        """ test validate_config() if CHARACTERS is not a list """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        mock_settings = Container()
        setattr(mock_settings, 'DEFAULT_SIMC', 'foo')
        setattr(mock_settings, 'CHARACTERS', 'foo')
        setattr(s, 'settings', mock_settings)
        with pytest.raises(SystemExit) as excinfo:
            res = s.validate_config()
        assert excinfo.value.code == 1
        assert mocklog.error.call_args_list == [call("ERROR: Settings file must define CHARACTERS list")]

    def test_validate_config_characters_empty(self, mock_ns):
        """ test validate_config() if CHARACTERS is an empty list """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        mock_settings = Container()
        setattr(mock_settings, 'DEFAULT_SIMC', 'foo')
        setattr(mock_settings, 'CHARACTERS', [])
        setattr(s, 'settings', mock_settings)
        with pytest.raises(SystemExit) as excinfo:
            res = s.validate_config()
        assert excinfo.value.code == 1
        assert mocklog.error.call_args_list == [call("ERROR: Settings file must define CHARACTERS list with at least one character")]

    @pytest.mark.skipif(sys.version_info >= (3,3), reason="requires python < 3.3")
    def test_import_from_path_py27(self, mock_ns):
        """ test import_from_path() under py27 """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        # this is a bit of a hack...
        settings_mock = Mock()
        imp_mock = Mock()
        ls_mock = Mock()
        ls_mock.return_value = settings_mock
        imp_mock.load_source = ls_mock
        sys.modules['imp'] = imp_mock
        with patch('autosimcraft.autosimcraft.imp', imp_mock):
            s.import_from_path('foobar')
            assert s.settings == settings_mock
        assert call('importing foobar - <py33') in mocklog.debug.call_args_list
        assert ls_mock.call_args_list == [call('settings', 'foobar')]
        assert call('imported settings module') in mocklog.debug.call_args_list

    @pytest.mark.skipif(sys.version_info < (3,3), reason="requires python3.3")
    def test_import_from_path_py33(self, mock_ns):
        """ test import_from_path() under py33 """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        settings_mock = Mock()
        machinery_mock = Mock()
        sfl_mock = Mock()
        loader_mock = Mock()
        loader_mock.load_module.return_value = settings_mock
        sfl_mock.return_value = loader_mock
        machinery_mock.SourceFileLoader = sfl_mock
        importlib_mock = Mock()
        autosimcraft.sys.modules['importlib'] = importlib_mock
        sys.modules['importlib.machinery'] = machinery_mock
        
        with patch('autosimcraft.autosimcraft.importlib.machinery', machinery_mock):
            s.import_from_path('foobar')
            assert s.settings == settings_mock
        assert call('importing foobar - <py33') in mocklog.debug.call_args_list
        assert ls_mock.call_args_list == [call('settings', 'foobar')]
        assert call('imported settings module') in mocklog.debug.call_args_list

    def test_validate_character(self, mock_ns):
        """ test validate_character() with correct character """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        char = {'realm': 'rname', 'name': 'cname'}
        result = s.validate_character(char)
        assert result is True

    def test_validate_character_notdict(self, mock_ns):
        """ test validate_character() where char is not a dict """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        char = 'realm'
        mocklog.debug.reset_mock()
        result = s.validate_character(char)
        assert mocklog.debug.call_args_list == [call('Character is not a dict')]
        assert result is False

    def test_validate_character_no_realm(self, mock_ns):
        """ test validate_character() with character missing realm """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        char = {'name': 'cname'}
        mocklog.debug.reset_mock()
        result = s.validate_character(char)
        assert mocklog.debug.call_args_list == [call("'realm' not in char dict")]
        assert result is False

    def test_validate_character_no_char(self, mock_ns):
        """ test validate_character() with character missing name """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        char = {'realm': 'rname'}
        mocklog.debug.reset_mock()
        result = s.validate_character(char)
        assert mocklog.debug.call_args_list == [call("'name' not in char dict")]
        assert result is False

    def test_run(self, mock_ns):
        """ test run() in ideal/working situation """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        chars = [{'name': 'nameone', 'realm': 'realmone', 'email': 'foo@example.com'}]
        s_container = Container()
        setattr(s_container, 'CHARACTERS', chars)
        setattr(s, 'settings', s_container)
        mocklog.debug.reset_mock()
        with nested(
                patch('autosimcraft.autosimcraft.AutoSimcraft.validate_character'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.get_battlenet'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.do_character'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.character_has_changes'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.write_character_cache'),
        ) as (mock_validate, mock_get_bnet, mock_do_char, mock_chc, mock_wcc):
            mock_chc.return_value = 'foo'
            mock_validate.return_value = True
            mock_get_bnet.return_value = {}
            s.run()
        assert mocklog.debug.call_args_list == [call("Doing character: nameone@realmone")]
        assert mock_validate.call_args_list == [call(chars[0])]
        assert mock_get_bnet.call_args_list == [call('realmone', 'nameone')]
        assert mock_do_char.call_args_list == [call('nameone@realmone', chars[0], 'foo')]
        assert mock_chc.call_args_list == [call('nameone@realmone', {})]
        assert mock_wcc.call_args_list == [call()]

    def test_run_invalid_character(self, mock_ns):
        """ test run() with an invalid character """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        chars = [{'name': 'nameone', 'realm': 'realmone', 'email': 'foo@example.com'}]
        s_container = Container()
        setattr(s_container, 'CHARACTERS', chars)
        setattr(s, 'settings', s_container)
        mocklog.debug.reset_mock()
        with nested(
                patch('autosimcraft.autosimcraft.AutoSimcraft.validate_character'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.get_battlenet'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.do_character'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.character_has_changes'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.write_character_cache'),
        ) as (mock_validate, mock_get_bnet, mock_do_char, mock_chc, mock_wcc):
            mock_chc.return_value = None
            mock_validate.return_value = False
            mock_get_bnet.return_value = {}
            s.run()
        assert mocklog.debug.call_args_list == [call("Doing character: nameone@realmone")]
        assert mock_validate.call_args_list == [call(chars[0])]
        assert mock_get_bnet.call_args_list == []
        assert mocklog.warning.call_args_list == [call("Character configuration not valid, skipping: nameone@realmone")]
        assert mock_do_char.call_args_list == []
        assert mock_chc.call_args_list == []
        assert mock_wcc.call_args_list == []

    def test_run_no_battlenet(self, mock_ns):
        """ test run() with character not found on battlenet """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        chars = [{'name': 'nameone', 'realm': 'realmone', 'email': 'foo@example.com'}]
        s_container = Container()
        setattr(s_container, 'CHARACTERS', chars)
        setattr(s, 'settings', s_container)
        mocklog.debug.reset_mock()
        with nested(
                patch('autosimcraft.autosimcraft.AutoSimcraft.validate_character'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.get_battlenet'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.do_character'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.character_has_changes'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.write_character_cache'),
        ) as (mock_validate, mock_get_bnet, mock_do_char, mock_chc, mock_wcc):
            mock_validate.return_value = True
            mock_get_bnet.return_value = None
            mock_chc.return_value = True
            s.run()
        assert mocklog.debug.call_args_list == [call("Doing character: nameone@realmone")]
        assert mock_validate.call_args_list == [call(chars[0])]
        assert mock_get_bnet.call_args_list == [call('realmone', 'nameone')]
        assert mocklog.warning.call_args_list == [call("Character nameone@realmone not found on battlenet; skipping.")]
        assert mock_do_char.call_args_list == []
        assert mock_chc.call_args_list == []
        assert mock_wcc.call_args_list == []

    def test_run_not_updated(self, mock_ns):
        """ test run() with no updates to character """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        chars = [{'name': 'nameone', 'realm': 'realmone', 'email': 'foo@example.com'}]
        s_container = Container()
        setattr(s_container, 'CHARACTERS', chars)
        setattr(s, 'settings', s_container)
        mocklog.debug.reset_mock()
        with nested(
                patch('autosimcraft.autosimcraft.AutoSimcraft.validate_character'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.get_battlenet'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.do_character'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.character_has_changes'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.write_character_cache'),
        ) as (mock_validate, mock_get_bnet, mock_do_char, mock_chc, mock_wcc):
            mock_chc.return_value = None
            mock_validate.return_value = True
            mock_get_bnet.return_value = {}
            s.run()
        assert mocklog.debug.call_args_list == [call("Doing character: nameone@realmone")]
        assert mock_validate.call_args_list == [call(chars[0])]
        assert mock_get_bnet.call_args_list == [call('realmone', 'nameone')]
        assert mock_do_char.call_args_list == []
        assert mock_chc.call_args_list == [call('nameone@realmone', {})]
        assert mock_wcc.call_args_list == [call()]

    def test_get_battlenet(self, mock_ns, mock_bnet_character):
        """ test get_battlenet() """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        conn.get_character.return_value = mock_bnet_character
        result = s.get_battlenet('rname', 'cname')
        assert conn.get_character.call_args_list == [call(battlenet.UNITED_STATES,
                                                 'rname',
                                                 'cname'
                                                 )
        ]
        for i in ['connection', 'achievementPoints', 'lastModified', '_items', 'achievement_points']:
            assert i not in result
        assert result['stats']['spellCrit'] == 12.5        
        assert 'recipes' not in result['professions']['primary'][0]
        assert result['name'] == 'Jantman'
        assert result['level'] == 100
        assert result['professions']['primary'][0] == {u'name': u'Tailoring',
                                                       u'max': 675,
                                                       u'rank': 627,
                                                       u'id': 197,
                                                       u'icon': u'trade_tailoring'
        }
        assert result['realm'] == 'Area 52'
        assert result['class'] == 9
        assert result['race'] == 5
        assert result['stats']['critRating'] == 825
        assert result['items']['shoulder']['id'] == 115997
        assert result['talents'][0]['talents'][0]['spell']['name'] == u'Soul Leech'

    def test_get_battlenet_badchar(self, mock_ns, mock_bnet_character):
        """ test get_battlenet() with character not found """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        conn.get_character.side_effect = battlenet.exceptions.CharacterNotFound()
        result = s.get_battlenet('rname', 'cname')
        assert conn.get_character.call_args_list == [call(battlenet.UNITED_STATES,
                                                 'rname',
                                                 'cname'
                                                 )
        ]
        assert result is None
        assert mocklog.error.call_args_list == [call("ERROR - Character Not Found - realm='rname' character='cname'")]

    def test_load_char_cache_noexist(self, mock_ns):
        """ test load_character_cache() on nonexistent file """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        mocko = mock_open()
        with nested(
                patch('autosimcraft.autosimcraft.os.path.exists'),
                patch('autosimcraft.autosimcraft.open', mocko, create=True),
        ) as (mock_fexist, m):
            mock_fexist.return_value = False
            res = s.load_character_cache()
        assert mocko.mock_calls == []
        assert mock_fexist.call_args_list == [call('/home/user/.autosimcraft/characters.pkl')]
        assert res == {}

    def test_load_char_cache(self, mock_ns):
        """ test load_character_cache() """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        with nested(
                patch('autosimcraft.autosimcraft.os.path.exists'),
                patch('autosimcraft.autosimcraft.open', create=True),
                patch('autosimcraft.autosimcraft.pickle.load')
        ) as (mock_fexist, mocko, mock_pkl):
            mock_fexist.return_value = True
            mocko.return_value = 'filecontents'
            mock_pkl.return_value = 'unpickled'
            res = s.load_character_cache()
        assert mocko.mock_calls == [call('/home/user/.autosimcraft/characters.pkl', 'rb')]
        assert mock_pkl.mock_calls == [call('filecontents')]
        assert mock_fexist.call_args_list == [call('/home/user/.autosimcraft/characters.pkl')]
        assert res == 'unpickled'

    def test_write_char_cache(self, mock_ns):
        """ test write_character_cache() """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        cache_content = {"foo": "bar", "baz": 3}
        openmock = MagicMock()
        with nested(
                patch('autosimcraft.autosimcraft.open', create=True),
                patch('autosimcraft.autosimcraft.pickle.dump')
        ) as (mocko, mock_pkl):
            mocko.return_value = openmock
            s.character_cache = deepcopy(cache_content)
            s.write_character_cache()
        assert mocko.mock_calls == [call('/home/user/.autosimcraft/characters.pkl', 'wb'),
                                    call().__enter__(),
                                    call().__exit__(None, None, None)]
        assert mock_pkl.mock_calls == [call(cache_content, openmock.__enter__())]

    def test_char_has_changes_true(self, mock_ns, char_data):
        """ test character_has_changes() with changes """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        orig_data = char_data
        cname = char_data['name'] + '@' + char_data['realm']
        ccache = {cname: orig_data}
        new_data = deepcopy(orig_data)
        new_data['items']['shoulder'] = {u'stats': [{u'stat': 59, u'amount': 60}, {u'stat': 32, u'amount': 80}, {u'stat': 5, u'amount': 109}, {u'stat': 7, u'amount': 163}], u'name': u'Mantle of Hooded Nightmares of the Savage', u'tooltipParams': {}, u'armor': 60, u'quality': 3, u'itemLevel': 615, u'context': u'dungeon-normal', u'bonusLists': [83], u'id': 114395, u'icon': u'inv_cloth_draenordungeon_c_01shoulder'}
        s.character_cache = ccache
        with patch('autosimcraft.autosimcraft.AutoSimcraft.character_diff') as mock_char_diff:
            mock_char_diff.return_value = 'foobar'
            result = s.character_has_changes(cname, new_data)
        assert result == 'foobar'
        assert mock_char_diff.call_args_list == [call(orig_data, new_data)]

    def test_character_diff_item(self, mock_ns, char_data):
        """ test character_diff() """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        cname = char_data['name'] + '@' + char_data['realm']
        ccache = {cname: char_data}
        new_data = deepcopy(char_data)
        new_data['items']['shoulder'] = {u'stats': [{u'stat': 59, u'amount': 60}, {u'stat': 32, u'amount': 80}, {u'stat': 5, u'amount': 109}, {u'stat': 7, u'amount': 163}], u'name': u'Mantle of Hooded Nightmares of the Savage', u'tooltipParams': {}, u'armor': 60, u'quality': 3, u'itemLevel': 615, u'context': u'dungeon-normal', u'bonusLists': [83], u'id': 114395, u'icon': u'inv_cloth_draenordungeon_c_01shoulder'}
        s.character_cache = ccache
        result = s.character_diff(char_data, new_data)
        expected = ["change items.shoulder.context from raid-finder to dungeon-normal",
                    "change [u'items', u'shoulder', u'stats', 0, u'stat'] from 32 to 59",
                    "change [u'items', u'shoulder', u'stats', 0, u'amount'] from 104 to 60",
                    "change [u'items', u'shoulder', u'stats', 1, u'stat'] from 5 to 32",
                    "change [u'items', u'shoulder', u'stats', 1, u'amount'] from 138 to 80",
                    "change [u'items', u'shoulder', u'stats', 2, u'stat'] from 36 to 5",
                    "change [u'items', u'shoulder', u'stats', 2, u'amount'] from 72 to 109",
                    "change [u'items', u'shoulder', u'stats', 3, u'amount'] from 207 to 163",
                    "change items.shoulder.name from Twin-Gaze Spaulders to Mantle of Hooded Nightmares of the Savage",
                    "remove items.shoulder.tooltipParams [(u'transmogItem', 31054)]",
                    "change items.shoulder.armor from 71 to 60",
                    "change items.shoulder.quality from 4 to 3",
                    "change items.shoulder.icon from inv_shoulder_cloth_draenorlfr_c_01 to inv_cloth_draenordungeon_c_01shoulder",
                    "change items.shoulder.itemLevel from 640 to 615",
                    "change items.shoulder.id from 115997 to 114395",
                    "add items.shoulder.bonusLists [(0, 83)]",
                    ]
        expected_s = "\n".join(sorted(expected))
        assert result == expected_s

    def test_char_has_changes_false(self, mock_ns, char_data):
        """ test character_has_changes() without changes """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        orig_data = char_data
        cname = char_data['name'] + '@' + char_data['realm']
        ccache = {cname: orig_data}
        new_data = deepcopy(orig_data)
        s.character_cache = ccache
        result = s.character_has_changes(cname, new_data)
        assert result is None

    def test_char_has_changes_new(self, mock_ns, char_data):
        """ test character_has_changes() on never-before-seen character """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        orig_data = char_data
        cname = char_data['name'] + '@' + char_data['realm']
        ccache = {}
        new_data = deepcopy(orig_data)
        s.character_cache = ccache
        result = s.character_has_changes(cname, new_data)
        assert result == "Character not in cache (has not been seen before)."

    def test_do_character_no_simc(self, mock_ns):
        """ test do_character() with SIMC_PATH non-existant """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_name = 'cname@rname'
        c_settings = {'realm': 'rname', 'name': 'cname', 'email': ['foo@example.com']}
        c_diff = 'diffcontent'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        
        first_dt = False
        def mock_dtnow_se(*args, **kwargs):
            if first_dt:
                return datetime.datetime(2014, 1, 1, 0, 0, 0)
            return datetime.datetime(2014, 1, 1, 1, 2, 3)
        def mock_ope_se(p):
            return False
        with nested(
                patch('autosimcraft.autosimcraft.os.path.exists'),
                patch('autosimcraft.autosimcraft.open', create=True),
                patch('autosimcraft.autosimcraft.os.chdir'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.now'),
                patch('autosimcraft.autosimcraft.subprocess.check_output'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.send_char_email'),
        ) as (mock_ope, mocko, mock_chdir, mock_dtnow, mock_subp, mock_sce):
            mock_ope.side_effect = mock_ope_se
            mock_dtnow.side_effect = mock_dtnow_se
            s.settings = settings
            s.do_character(c_name, c_settings, c_diff)
        assert mock_ope.call_args_list == [call('/path/to/simc')]
        assert mocko.mock_calls == []
        assert mock_chdir.call_args_list == []
        assert mock_subp.call_args_list == []
        assert mock_sce.call_args_list == []
        assert mocklog.error.call_args_list == [call('ERROR: simc path /path/to/simc does not exist')]

    def test_do_character(self, mock_ns):
        """ test do_character() in normal case """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_name = 'cname@rname'
        c_settings = {'realm': 'rname', 'name': 'cname', 'email': ['foo@example.com']}
        c_diff = 'diffcontent'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        
        def mock_ope_se(p):
            return True

        with nested(
                patch('autosimcraft.autosimcraft.os.path.exists'),
                patch('autosimcraft.autosimcraft.open', create=True),
                patch('autosimcraft.autosimcraft.os.chdir'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.now'),
                patch('autosimcraft.autosimcraft.subprocess.check_output'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.send_char_email'),
        ) as (mock_ope, mocko, mock_chdir, mock_dtnow, mock_subp, mock_sce):
            mock_ope.side_effect = mock_ope_se
            mock_dtnow.side_effect = [datetime.datetime(2014, 1, 1, 0, 0, 0), datetime.datetime(2014, 1, 1, 1, 2, 3)]
            mock_subp.return_value = 'subprocessoutput'
            s.settings = settings
            s.do_character(c_name, c_settings, c_diff)
        assert mock_ope.call_args_list == [call('/path/to/simc'), call('/home/user/.autosimcraft/cname@rname.html')]
        assert mocko.mock_calls == [call('/home/user/.autosimcraft/cname@rname.simc', 'w'),
                                    call().__enter__(),
                                    call().__enter__().write('"armory=us,rname,cname"\n'),
                                    call().__enter__().write('calculate_scale_factors=1\n'),
                                    call().__enter__().write('html=cname@rname.html'),
                                    call().__exit__(None, None, None)]
        assert mock_chdir.call_args_list == [call('/home/user/.autosimcraft')]
        assert mock_subp.call_args_list == [call(['/path/to/simc',
                                                  '/home/user/.autosimcraft/cname@rname.simc'],
                                                 stderr=subprocess.STDOUT)]
        assert mock_sce.call_args_list == [call('cname@rname',
                                                {'realm': 'rname', 'name': 'cname', 'email': ['foo@example.com']},
                                                'diffcontent',
                                                '/home/user/.autosimcraft/cname@rname.html',
                                                datetime.timedelta(seconds=3723),
                                                'subprocessoutput')]
        assert mocklog.error.call_args_list == []

    def test_do_character_simc_error(self, mock_ns):
        """ test do_character() with simc exiting non-0 """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_name = 'cname@rname'
        c_settings = {'realm': 'rname', 'name': 'cname', 'email': ['foo@example.com']}
        c_diff = 'diffcontent'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        
        def mock_ope_se(p):
            return True

        with nested(
                patch('autosimcraft.autosimcraft.os.path.exists'),
                patch('autosimcraft.autosimcraft.open', create=True),
                patch('autosimcraft.autosimcraft.os.chdir'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.now'),
                patch('autosimcraft.autosimcraft.subprocess.check_output'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.send_char_email'),
        ) as (mock_ope, mocko, mock_chdir, mock_dtnow, mock_subp, mock_sce):
            mock_ope.side_effect = mock_ope_se
            mock_dtnow.side_effect = [datetime.datetime(2014, 1, 1, 0, 0, 0), datetime.datetime(2014, 1, 1, 1, 2, 3)]
            mock_subp.side_effect = subprocess.CalledProcessError(1, 'command', 'erroroutput')
            s.settings = settings
            s.do_character(c_name, c_settings, c_diff)
        assert mock_ope.call_args_list == [call('/path/to/simc')]
        assert mocko.mock_calls == [call('/home/user/.autosimcraft/cname@rname.simc', 'w'),
                                    call().__enter__(),
                                    call().__enter__().write('"armory=us,rname,cname"\n'),
                                    call().__enter__().write('calculate_scale_factors=1\n'),
                                    call().__enter__().write('html=cname@rname.html'),
                                    call().__exit__(None, None, None)]
        assert mock_chdir.call_args_list == [call('/home/user/.autosimcraft')]
        assert mock_subp.call_args_list == [call(['/path/to/simc',
                                                  '/home/user/.autosimcraft/cname@rname.simc'],
                                                 stderr=subprocess.STDOUT)]
        assert mock_sce.call_args_list == []
        assert mocklog.error.call_args_list == [call('Error running simc!')]

    def test_do_character_no_html(self, mock_ns):
        """ do_character() - simc runs but HTML not created """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_name = 'cname@rname'
        c_settings = {'realm': 'rname', 'name': 'cname', 'email': ['foo@example.com']}
        c_diff = 'diffcontent'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        
        def mock_ope_se(p):
            if p == '/home/user/.autosimcraft/cname@rname.html':
                return False
            return True

        with nested(
                patch('autosimcraft.autosimcraft.os.path.exists'),
                patch('autosimcraft.autosimcraft.open', create=True),
                patch('autosimcraft.autosimcraft.os.chdir'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.now'),
                patch('autosimcraft.autosimcraft.subprocess.check_output'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.send_char_email'),
        ) as (mock_ope, mocko, mock_chdir, mock_dtnow, mock_subp, mock_sce):
            mock_ope.side_effect = mock_ope_se
            mock_dtnow.side_effect = [datetime.datetime(2014, 1, 1, 0, 0, 0), datetime.datetime(2014, 1, 1, 1, 2, 3)]
            mock_subp.return_value = 'simcoutput'
            s.settings = settings
            s.do_character(c_name, c_settings, c_diff)
        assert mock_ope.call_args_list == [call('/path/to/simc'), call('/home/user/.autosimcraft/cname@rname.html')]
        assert mocko.mock_calls == [call('/home/user/.autosimcraft/cname@rname.simc', 'w'),
                                    call().__enter__(),
                                    call().__enter__().write('"armory=us,rname,cname"\n'),
                                    call().__enter__().write('calculate_scale_factors=1\n'),
                                    call().__enter__().write('html=cname@rname.html'),
                                    call().__exit__(None, None, None)]
        assert mock_chdir.call_args_list == [call('/home/user/.autosimcraft')]
        assert mock_subp.call_args_list == [call(['/path/to/simc',
                                                  '/home/user/.autosimcraft/cname@rname.simc'],
                                                 stderr=subprocess.STDOUT)]
        assert mock_sce.call_args_list == []
        assert mocklog.error.call_args_list == [call('ERROR: simc finished but HTML file not found on disk.')]

    def test_send_char_email(self, mock_ns):
        """ test send_char_email() in normal case """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_settings = {'realm': 'rname', 'name': 'cname', 'email': ['foo@example.com']}
        c_name = 'cname@rname'
        c_diff = 'diffcontent'
        html_path = '/path/to/output.html'
        duration = datetime.timedelta(seconds=3723)  # 1h 2m 3s
        output = 'simc_output_string'
        subj = 'SimulationCraft output for cname@rname'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        with nested(
                patch('autosimcraft.autosimcraft.AutoSimcraft.send_gmail'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.format_message', spec_set=MIMEMultipart),
                patch('autosimcraft.autosimcraft.AutoSimcraft.send_local'),
                patch('autosimcraft.autosimcraft.platform.node'),
                patch('autosimcraft.autosimcraft.getpass.getuser'),

        ) as (mock_gmail, mock_format, mock_local, mock_node, mock_user):
            mock_node.return_value = 'nodename'
            mock_user.return_value = 'username'
            mock_format.return_value.as_string.return_value = 'msgbody'
            s.settings = settings
            s.send_char_email(c_name,
                              c_settings,
                              c_diff,
                              html_path,
                              duration,
                              output)
        assert mock_format.call_args_list == [call('username@nodename',
                                                   'foo@example.com',
                                                   subj,
                                                   c_name,
                                                   c_diff,
                                                   html_path,
                                                   duration,
                                                   output)]
        assert mock_local.call_args_list == [call('username@nodename',
                                                  'foo@example.com',
                                                  'msgbody')]
        assert mock_gmail.call_args_list == []

    def test_send_char_string_email(self, mock_ns):
        """ test send_char_email() with email as a string """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_settings = {'realm': 'rname',
                      'name': 'cname',
                      'email': 'foo@example.com'}
        c_name = 'cname@rname'
        c_diff = 'diffcontent'
        html_path = '/path/to/output.html'
        duration = datetime.timedelta(seconds=3723)  # 1h 2m 3s
        output = 'simc_output_string'
        subj = 'SimulationCraft output for cname@rname'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        with nested(
                patch('autosimcraft.autosimcraft.AutoSimcraft.send_gmail'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.format_message', spec_set=MIMEMultipart),
                patch('autosimcraft.autosimcraft.AutoSimcraft.send_local'),
                patch('autosimcraft.autosimcraft.platform.node'),
                patch('autosimcraft.autosimcraft.getpass.getuser'),
        ) as (mock_gmail, mock_format, mock_local, mock_node, mock_user):
            mock_node.return_value = 'nodename'
            mock_user.return_value = 'username'
            mock_format.return_value.as_string.return_value = 'msgbody'
            s.settings = settings
            s.send_char_email(c_name,
                              c_settings,
                              c_diff,
                              html_path,
                              duration,
                              output)
        assert mock_format.call_args_list == [call('username@nodename',
                                                   'foo@example.com',
                                                   subj,
                                                   c_name,
                                                   c_diff,
                                                   html_path,
                                                   duration,
                                                   output)]
        assert mock_local.call_args_list == [call('username@nodename',
                                                  'foo@example.com',
                                                  'msgbody')]
        assert mock_gmail.call_args_list == []

    def test_send_char_email_gmail(self, mock_ns):
        """ test send_char_email() via gmail """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_settings = {'realm': 'rname',
                      'name': 'cname',
                      'email': 'foo@example.com'}
        c_name = 'cname@rname'
        c_diff = 'diffcontent'
        html_path = '/path/to/output.html'
        duration = datetime.timedelta(seconds=3723)  # 1h 2m 3s
        output = 'simc_output_string'
        subj = 'SimulationCraft output for cname@rname'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        setattr(settings, 'GMAIL_USERNAME', 'gmailuser')
        setattr(settings, 'GMAIL_PASSWORD', 'gmailpass')
        with nested(
                patch('autosimcraft.autosimcraft.AutoSimcraft.send_gmail'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.format_message', spec_set=MIMEMultipart),
                patch('autosimcraft.autosimcraft.AutoSimcraft.send_local'),
                patch('autosimcraft.autosimcraft.platform.node'),
                patch('autosimcraft.autosimcraft.getpass.getuser'),
        ) as (mock_gmail, mock_format, mock_local, mock_node, mock_user):
            mock_node.return_value = 'nodename'
            mock_user.return_value = 'username'
            mock_format.return_value.as_string.return_value = 'msgbody'
            s.settings = settings
            s.send_char_email(c_name,
                              c_settings,
                              c_diff,
                              html_path,
                              duration,
                              output)
        assert mock_format.call_args_list == [call('username@nodename',
                                                   'foo@example.com',
                                                   subj,
                                                   c_name,
                                                   c_diff,
                                                   html_path,
                                                   duration,
                                                   output)]
        assert mock_gmail.call_args_list == [call('username@nodename',
                                                  'foo@example.com',
                                                  'msgbody')]
        assert mock_local.call_args_list == []

    def test_send_char_email_dryrun(self, mock_ns):
        """ test send_char_email() for a dry run """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_settings = {'realm': 'rname',
                      'name': 'cname',
                      'email': ['foo@example.com']}
        c_name = 'cname@rname'
        c_diff = 'diffcontent'
        html_path = '/path/to/output.html'
        duration = datetime.timedelta(seconds=3723)  # 1h 2m 3s
        output = 'simc_output_string'
        subj = 'SimulationCraft output for cname@rname'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        with nested(
                patch('autosimcraft.autosimcraft.AutoSimcraft.send_gmail'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.format_message', spec_set=MIMEMultipart),
                patch('autosimcraft.autosimcraft.AutoSimcraft.send_local'),
                patch('autosimcraft.autosimcraft.platform.node'),
                patch('autosimcraft.autosimcraft.getpass.getuser'),
        ) as (mock_gmail, mock_format, mock_local, mock_node, mock_user):
            mock_node.return_value = 'nodename'
            mock_user.return_value = 'username'
            mock_format.as_string.return_value = 'msgbody'
            s.settings = settings
            s.dry_run = True
            s.send_char_email(c_name,
                              c_settings,
                              c_diff,
                              html_path,
                              duration,
                              output)
        assert mocklog.info.call_args_list == [call("Sending email for character cname@rname to foo@example.com")]
        assert mocklog.warning.call_args_list == [call("DRY RUN - not actually sending email")]
        assert mock_format.call_args_list == []
        assert mock_local.call_args_list == []
        assert mock_gmail.call_args_list == []

    def test_format_message(self, mock_ns):
        """ test format_message() """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        dest_addr = 'foo@example.com'
        subj = 'mysubj'
        c_name = 'cname@rname'
        c_diff = 'characterDiffHere'
        html_path = '/path/to/file.html'
        duration = datetime.timedelta(seconds=3723)  # 1h 2m 3s
        output = 'simcoutput'
        from_addr = 'from@me'
        htmlcontent = '<html><head><title>foo</title></head><body>bar</body></html>'
        expected = 'SimulationCraft was run for cname@rname due to the following changes:\n'
        expected += '\ncharacterDiffHere\n\n'
        expected += 'The run was completed in 1:02:03 and the HTML report is attached'
        expected += '. (Note that you likely need to save the HTML attachment to disk and'
        expected += ' view it from there; it will not render correctly in most email clients.)\n\n'
        expected += 'SimulationCraft output: \n\nsimcoutput\n\n'
        expected += 'This run was done on nodename at 2014-01-01 00:00:00 by autosimcraft.py va.b.c'
        with nested(
                patch('autosimcraft.autosimcraft.platform.node'),
                patch('autosimcraft.autosimcraft.AutoSimcraft.now'),
                patch('autosimcraft.autosimcraft.open', create=True)
        ) as (mock_node, mock_now, mock_open):
            mock_node.return_value = 'nodename'
            mock_now.return_value = datetime.datetime(2014, 1, 1, 0, 0, 0)
            mock_open.return_value = MagicMock(spec=file)
            with patch.object(s, 'VERSION', 'a.b.c'):
                mock_open.return_value.__enter__.return_value.read.return_value = htmlcontent
                res = s.format_message(from_addr,
                                       dest_addr,
                                       subj,
                                       c_name,
                                       c_diff,
                                       html_path,
                                       duration,
                                       output)
        assert res['Subject'] == subj
        assert res['To'] == dest_addr
        assert res['From'] == 'AutoSimcraft <{f}>'.format(f=from_addr)
        assert res._payload[0]._payload == expected
        #assert res._payload[1]._payload == htmlcontent
        assert b64decode(res._payload[1]._payload) == htmlcontent
        file_handle = mock_open.return_value.__enter__.return_value
        assert mock_open.call_args_list == [call('/path/to/file.html', 'r')]
        assert file_handle.read.call_count == 1

    def test_send_local(self, mock_ns):
        """ send_local() test """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        with nested(
                patch('autosimcraft.autosimcraft.smtplib.SMTP', autospec=True),
        ) as (mock_smtp, ):
            s.send_local('from', 'to', 'msg')
        assert mock_smtp.mock_calls == [call('localhost'),
                                        call().sendmail('from', ['to'], 'msg'),
                                        call().quit()
        ]

    def test_send_gmail(self, mock_ns):
        """ send_gmail() test """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        settings = Container()
        setattr(settings, 'GMAIL_USERNAME', 'myusername')
        setattr(settings, 'GMAIL_PASSWORD', 'mypassword')
        with nested(
                patch('autosimcraft.autosimcraft.smtplib.SMTP', autospec=True),
        ) as (mock_smtp, ):
            s.settings = settings
            s.send_gmail('from', 'to', 'msg')
        assert mock_smtp.mock_calls == [call('smtp.gmail.com:587'),
                                        call().starttls(),
                                        call().login('myusername', 'mypassword'),
                                        call().sendmail('from', ['to'], 'msg'),
                                        call().quit()
        ]

    def test_make_char_name(self, mock_ns):
        """ make_character_name() tests """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        assert s.make_character_name('n', 'r') == 'n@r'
        assert s.make_character_name('MyName', 'MyRealm') == 'MyName@MyRealm'
        assert s.make_character_name('sómÊñámé', 'Area 52') == 'sómÊñámé@Area52'
        
    @freeze_time("2014-01-01 01:02:03")
    def test_now(self, mock_ns):
        bn, rc, mocklog, s, conn, lcc = mock_ns
        result = s.now()
        assert result == datetime.datetime(2014, 1, 1, 1, 2, 3)
