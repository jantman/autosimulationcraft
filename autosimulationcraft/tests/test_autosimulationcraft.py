# -*- coding: utf-8 -*-
"""
AutoSimulationCraft - tests for AutoSimulationCraft class

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

import pytest
import logging
from mock import MagicMock, call, patch, Mock, mock_open
import sys
import os
import datetime
from copy import deepcopy
import subprocess
from email.mime.multipart import MIMEMultipart
from base64 import b64decode

from freezegun import freeze_time
import battlenet

from autosimulationcraft import autosimulationcraft
from data_fixtures import bnet_data, char_data
from fixtures import Container, mock_ns, mock_bnet_character


def test_default_confdir():
    assert autosimulationcraft.DEFAULT_CONFDIR == '~/.autosimulationcraft'


def make_flakes_happy():
    """
    hack to make flakes think fixtures are used.
    this function never gets executed.
    """
    a = mock_ns
    b = bnet_data
    c = char_data
    d = mock_bnet_character
    print(a, b, c, d)


class Test_AutoSimulationCraft:

    def test_init_default(self):
        """ test SimpleScript.init() """
        bn = MagicMock(spec_set=battlenet.Connection)
        rc = Mock()
        with patch('autosimulationcraft.autosimulationcraft.'
                   'battlenet.Connection', bn), \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.read_config', rc):
            s = autosimulationcraft.AutoSimulationCraft(dry_run=False,
                                                        verbose=0,
                                                        confdir='~/.autosimulationcraft'
                                                        )
        assert bn.mock_calls == [call()]
        assert rc.call_args_list == [call('~/.autosimulationcraft')]
        assert s.dry_run is False
        assert isinstance(s.logger, logging.Logger)
        assert s.logger.level == logging.NOTSET

    def test_init_logger(self):
        """ test SimpleScript.init() with specified logger """
        m = MagicMock(spec_set=logging.Logger)
        bn = MagicMock(spec_set=battlenet.Connection)
        rc = Mock()
        with patch('autosimulationcraft.autosimulationcraft.'
                   'battlenet.Connection', bn), \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.read_config', rc):
            s = autosimulationcraft.AutoSimulationCraft(logger=m)
        assert s.logger == m

    def test_init_dry_run(self):
        """ test SimpleScript.init() with dry_run=True """
        bn = MagicMock(spec_set=battlenet.Connection)
        rc = Mock()
        with patch('autosimulationcraft.autosimulationcraft.'
                   'battlenet.Connection', bn), \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.read_config', rc):
            s = autosimulationcraft.AutoSimulationCraft(dry_run=True)
        assert s.dry_run is True

    def test_init_verbose(self):
        """ test SimpleScript.init() with verbose=1 """
        bn = MagicMock(spec_set=battlenet.Connection)
        rc = Mock()
        with patch('autosimulationcraft.autosimulationcraft.'
                   'battlenet.Connection', bn), \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.read_config', rc):
            s = autosimulationcraft.AutoSimulationCraft(verbose=1)
        assert s.logger.level == logging.INFO

    def test_init_debug(self):
        """ test SimpleScript.init() with verbose=2 """
        bn = MagicMock(spec_set=battlenet.Connection)
        rc = Mock()
        with patch('autosimulationcraft.autosimulationcraft.'
                   'battlenet.Connection', bn), \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.read_config', rc):
            s = autosimulationcraft.AutoSimulationCraft(verbose=2)
        assert s.logger.level == logging.DEBUG

    def test_read_config_missing(self, mock_ns):
        """ test read_config() when settings file is missing """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        with patch('autosimulationcraft.autosimulationcraft.'
                   'os.path.exists') as mock_path_exists, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.import_from_path') as mock_import, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.validate_config'):
            mock_path_exists.return_value = False
            with pytest.raises(SystemExit) as excinfo:
                s.read_config('/foo')
            assert excinfo.value.code == 1
        assert call(
            'Reading configuration from: /foo/settings.py') in mocklog.debug.call_args_list
        assert mock_import.call_count == 0
        assert mock_path_exists.call_count == 1
        assert mocklog.error.call_args_list == [
            call("ERROR - configuration file does not exist. "
                 "Please run with --genconfig to generate an example one.")]

    def test_read_config(self, mock_ns):
        """ test read_config() working correctly """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        mock_settings = Container()
        setattr(mock_settings, 'CHARACTERS', [])
        setattr(mock_settings, 'DEFAULT_SIMC', 'foo')
        setattr(s, 'settings', mock_settings)
        with patch('autosimulationcraft.autosimulationcraft.'
                   'os.path.exists') as mock_path_exists, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.import_from_path') as mock_import, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.validate_config') as mock_validate:
            mock_path_exists.return_value = True
            s.read_config('/foo')
        assert call(
            'Reading configuration from: /foo/settings.py') in mocklog.debug.call_args_list
        assert mock_import.call_args_list == [call('/foo/settings.py')]
        assert mock_path_exists.call_count == 1
        assert mock_validate.call_args_list == [call()]

    def test_genconfig(self):
        """ test gen_config() """
        cd = '/foo'
        with patch('autosimulationcraft.autosimulationcraft.'
                   'os.path.exists') as mock_pe, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=file)
            mock_pe.return_value = True
            autosimulationcraft.AutoSimulationCraft.gen_config(cd)
        file_handle = mock_open.return_value.__enter__.return_value
        assert mock_open.call_args_list == [call('/foo/settings.py', 'w')]
        assert file_handle.write.call_count == 1

    def test_genconfig_nodir(self):
        """ test gen_config() with config directory missing """
        cd = '/foo'
        with patch('autosimulationcraft.autosimulationcraft.'
                   'os.path.exists') as mock_pe, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'os.mkdir') as mock_mkdir, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=file)
            mock_pe.return_value = False
            autosimulationcraft.AutoSimulationCraft.gen_config(cd)
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
            s.validate_config()
        assert excinfo.value.code == 1
        assert mocklog.error.call_args_list == [
            call("ERROR: Settings file must define CHARACTERS list")]

    def test_validate_config_characters_not_list(self, mock_ns):
        """ test validate_config() if CHARACTERS is not a list """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        mock_settings = Container()
        setattr(mock_settings, 'DEFAULT_SIMC', 'foo')
        setattr(mock_settings, 'CHARACTERS', 'foo')
        setattr(s, 'settings', mock_settings)
        with pytest.raises(SystemExit) as excinfo:
            s.validate_config()
        assert excinfo.value.code == 1
        assert mocklog.error.call_args_list == [
            call("ERROR: Settings file must define CHARACTERS list")]

    def test_validate_config_characters_empty(self, mock_ns):
        """ test validate_config() if CHARACTERS is an empty list """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        mock_settings = Container()
        setattr(mock_settings, 'DEFAULT_SIMC', 'foo')
        setattr(mock_settings, 'CHARACTERS', [])
        setattr(s, 'settings', mock_settings)
        with pytest.raises(SystemExit) as excinfo:
            s.validate_config()
        assert excinfo.value.code == 1
        assert mocklog.error.call_args_list == [
            call("ERROR: Settings file must define CHARACTERS list with at least one character")]

    def test_validate_config_ok(self, mock_ns):
        """ test validate_config() with good config """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        mock_settings = Container()
        setattr(mock_settings, 'DEFAULT_SIMC', 'foo')
        setattr(mock_settings, 'CHARACTERS', ['foo'])
        setattr(s, 'settings', mock_settings)
        s.validate_config()
        assert mocklog.error.call_args_list == []

    @pytest.mark.skipif(
        sys.version_info >= (3, 3), reason="requires python < 3.3")
    def test_import_from_path_py27(self, mock_ns):
        """ test import_from_path() under py27 """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        fpath = os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)),
            'fixtures',
            'importtest.py')
        s.import_from_path(fpath)
        assert call(
            'importing {c} - <py33'.format(c=fpath)) in mocklog.debug.call_args_list
        assert call('imported settings module') in mocklog.debug.call_args_list
        assert s.settings.FOO == 'bar'
        assert s.settings.BAZ == ['blam', 'blarg']

    @pytest.mark.skipif(sys.version_info < (3, 3), reason="requires python3.3")
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
        autosimulationcraft.sys.modules['importlib'] = importlib_mock
        sys.modules['importlib.machinery'] = machinery_mock
        with patch('autosimulationcraft.autosimulationcraft.'
                   'importlib.machinery', machinery_mock):
            s.import_from_path('foobar')
            assert s.settings == settings_mock
        assert call('importing foobar - <py33') in mocklog.debug.call_args_list
        assert sfl_mock.call_args_list == [call('settings', 'foobar')]
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
        assert mocklog.debug.call_args_list == [
            call('Character is not a dict')]
        assert result is False

    def test_validate_character_no_realm(self, mock_ns):
        """ test validate_character() with character missing realm """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        char = {'name': 'cname'}
        mocklog.debug.reset_mock()
        result = s.validate_character(char)
        assert mocklog.debug.call_args_list == [
            call("'realm' not in char dict")]
        assert result is False

    def test_validate_character_no_char(self, mock_ns):
        """ test validate_character() with character missing name """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        char = {'realm': 'rname'}
        mocklog.debug.reset_mock()
        result = s.validate_character(char)
        assert mocklog.debug.call_args_list == [
            call("'name' not in char dict")]
        assert result is False

    def test_run(self, mock_ns):
        """ test run() in ideal/working situation """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        chars = [{'name': 'nameone',
                  'realm': 'realmone',
                  'email': 'foo@example.com'}]
        s_container = Container()
        ccache = {}
        setattr(s_container, 'CHARACTERS', chars)
        setattr(s, 'settings', s_container)
        setattr(s, 'character_cache', ccache)
        mocklog.debug.reset_mock()
        with patch('autosimulationcraft.autosimulationcraft.'
                   'AutoSimulationCraft.validate_character') as mock_validate, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.get_battlenet') as mock_get_bnet, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.do_character') as mock_do_char, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.character_has_changes') as mock_chc, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.write_character_cache') as mock_wcc:
            mock_chc.return_value = 'foo'
            mock_validate.return_value = True
            mock_get_bnet.return_value = {'foo': 'bar'}
            s.run()
        assert mocklog.debug.call_args_list == [
            call("Doing character: nameone@realmone")]
        assert mock_validate.call_args_list == [call(chars[0])]
        assert mock_get_bnet.call_args_list == [call('realmone', 'nameone')]
        assert mock_do_char.call_args_list == [
            call(
                'nameone@realmone',
                chars[0],
                'foo')]
        assert mock_chc.call_args_list == [
            call(
                'nameone@realmone', {
                    'foo': 'bar'}, no_stat=False)]
        assert mock_wcc.call_args_list == [call()]
        assert ccache == {'nameone@realmone': {'foo': 'bar'}}

    def test_run_invalid_character(self, mock_ns):
        """ test run() with an invalid character """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        chars = [{'name': 'nameone',
                  'realm': 'realmone',
                  'email': 'foo@example.com'}]
        s_container = Container()
        ccache = {}
        setattr(s_container, 'CHARACTERS', chars)
        setattr(s, 'settings', s_container)
        setattr(s, 'character_cache', ccache)
        mocklog.debug.reset_mock()
        with patch('autosimulationcraft.autosimulationcraft.'
                   'AutoSimulationCraft.validate_character') as mock_validate, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.get_battlenet') as mock_get_bnet, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.do_character') as mock_do_char, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.character_has_changes') as mock_chc, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.write_character_cache') as mock_wcc:
            mock_chc.return_value = None
            mock_validate.return_value = False
            mock_get_bnet.return_value = {}
            s.run()
        assert mocklog.debug.call_args_list == [
            call("Doing character: nameone@realmone")]
        assert mock_validate.call_args_list == [call(chars[0])]
        assert mock_get_bnet.call_args_list == []
        assert mocklog.warning.call_args_list == [
            call("Character configuration not valid, skipping: nameone@realmone")]
        assert mock_do_char.call_args_list == []
        assert mock_chc.call_args_list == []
        assert mock_wcc.call_args_list == []
        assert ccache == {}

    def test_run_no_battlenet(self, mock_ns):
        """ test run() with character not found on battlenet """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        chars = [{'name': 'nameone',
                  'realm': 'realmone',
                  'email': 'foo@example.com'}]
        s_container = Container()
        ccache = {}
        setattr(s_container, 'CHARACTERS', chars)
        setattr(s, 'settings', s_container)
        setattr(s, 'character_cache', ccache)
        mocklog.debug.reset_mock()
        with patch('autosimulationcraft.autosimulationcraft.'
                   'AutoSimulationCraft.validate_character') as mock_validate, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.get_battlenet') as mock_get_bnet, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.do_character') as mock_do_char, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.character_has_changes') as mock_chc, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.write_character_cache') as mock_wcc:
            mock_validate.return_value = True
            mock_get_bnet.return_value = None
            mock_chc.return_value = True
            s.run()
        assert mocklog.debug.call_args_list == [
            call("Doing character: nameone@realmone")]
        assert mock_validate.call_args_list == [call(chars[0])]
        assert mock_get_bnet.call_args_list == [call('realmone', 'nameone')]
        assert mocklog.warning.call_args_list == [
            call("Character nameone@realmone not found on battlenet; skipping.")]
        assert mock_do_char.call_args_list == []
        assert mock_chc.call_args_list == []
        assert mock_wcc.call_args_list == []
        assert ccache == {}

    def test_run_not_updated(self, mock_ns):
        """ test run() with no updates to character """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        chars = [{'name': 'nameone',
                  'realm': 'realmone',
                  'email': 'foo@example.com'}]
        s_container = Container()
        ccache = {}
        setattr(s_container, 'CHARACTERS', chars)
        setattr(s, 'settings', s_container)
        setattr(s, 'character_cache', ccache)
        mocklog.debug.reset_mock()
        with patch('autosimulationcraft.autosimulationcraft.'
                   'AutoSimulationCraft.validate_character') as mock_validate, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.get_battlenet') as mock_get_bnet, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.do_character') as mock_do_char, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.character_has_changes') as mock_chc, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.write_character_cache') as mock_wcc:
            mock_chc.return_value = None
            mock_validate.return_value = True
            mock_get_bnet.return_value = {'foo': 'bar'}
            s.run()
        assert mocklog.debug.call_args_list == [
            call("Doing character: nameone@realmone")]
        assert mock_validate.call_args_list == [call(chars[0])]
        assert mock_get_bnet.call_args_list == [call('realmone', 'nameone')]
        assert mock_do_char.call_args_list == []
        assert mock_chc.call_args_list == [
            call(
                'nameone@realmone', {
                    'foo': 'bar'}, no_stat=False)]
        assert mock_wcc.call_args_list == [call()]
        assert ccache == {'nameone@realmone': {'foo': 'bar'}}

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
        for i in ['connection', 'achievementPoints',
                  'lastModified', '_items', 'achievement_points']:
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
        assert result['talents'][0]['talents'][
            0]['spell']['name'] == u'Soul Leech'

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
        assert mocklog.error.call_args_list == [
            call("ERROR - Character Not Found - realm='rname' character='cname'")]

    def test_load_char_cache_noexist(self, mock_ns):
        """ test load_character_cache() on nonexistent file """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        mocko = mock_open()
        with patch('autosimulationcraft.autosimulationcraft.'
                   'os.path.exists') as mock_fexist, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'open', mocko, create=True):
            mock_fexist.return_value = False
            res = s.load_character_cache()
        assert mocko.mock_calls == []
        assert mock_fexist.call_args_list == [
            call('/home/user/.autosimulationcraft/characters.pkl')]
        assert res == {}

    def test_load_char_cache(self, mock_ns):
        """ test load_character_cache() """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        with patch('autosimulationcraft.autosimulationcraft.'
                   'os.path.exists') as mock_fexist, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'open', create=True) as mocko, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'pickle.load') as mock_pkl:
            mock_fexist.return_value = True
            mocko.return_value = 'filecontents'
            mock_pkl.return_value = 'unpickled'
            res = s.load_character_cache()
        assert mocko.mock_calls == [
            call(
                '/home/user/.autosimulationcraft/characters.pkl',
                'rb')]
        assert mock_pkl.mock_calls == [call('filecontents')]
        assert mock_fexist.call_args_list == [
            call('/home/user/.autosimulationcraft/characters.pkl')]
        assert res == 'unpickled'

    def test_write_char_cache(self, mock_ns):
        """ test write_character_cache() """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        cache_content = {"foo": "bar", "baz": 3}
        openmock = MagicMock()
        with patch('autosimulationcraft.autosimulationcraft.'
                   'open', create=True) as mocko, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'pickle.dump') as mock_pkl:
            mocko.return_value = openmock
            s.character_cache = deepcopy(cache_content)
            s.write_character_cache()
        assert mocko.mock_calls == [call('/home/user/.autosimulationcraft/characters.pkl', 'wb'),
                                    call().__enter__(),
                                    call().__exit__(None, None, None)]
        assert mock_pkl.mock_calls == [
            call(
                cache_content,
                openmock.__enter__())]

    def test_char_has_changes_true(self, mock_ns, char_data):
        """ test character_has_changes() with changes """
        bn, rc, mocklog, s, conn, lcc = mock_ns

        def fix_se(char, no_stat=False):
            return char

        orig_data = char_data
        cname = char_data['name'] + '@' + char_data['realm']
        ccache = {cname: orig_data}
        new_data = deepcopy(orig_data)
        new_data['items']['shoulder'] = {u'stats': [{u'stat': 59,
                                                     u'amount': 60},
                                                    {u'stat': 32,
                                                     u'amount': 80},
                                                    {u'stat': 5,
                                                     u'amount': 109},
                                                    {u'stat': 7,
                                                     u'amount': 163}],
                                         u'name': u'Mantle of Hooded Nightmares of the Savage',
                                         u'tooltipParams': {},
                                         u'armor': 60,
                                         u'quality': 3,
                                         u'itemLevel': 615,
                                         u'context': u'dungeon-normal',
                                         u'bonusLists': [83],
                                         u'id': 114395,
                                         u'icon': u'inv_cloth_draenordungeon_c_01shoulder'}
        s.character_cache = ccache
        with patch('autosimulationcraft.autosimulationcraft.'
                   'AutoSimulationCraft.character_diff') as mock_char_diff, \
            patch('autosimulationcraft.autosimulationcraft.'
                  'AutoSimulationCraft.fix_char_for_diff') as mock_fix_char:
            mock_fix_char.side_effect = fix_se
            mock_char_diff.return_value = 'foobar'
            result = s.character_has_changes(cname, new_data, no_stat=False)
        assert result == 'foobar'
        assert mock_fix_char.mock_calls == [
            call(new_data, no_stat=False),
            call(orig_data, no_stat=False),
        ]
        assert mock_char_diff.call_args_list == [call(orig_data, new_data)]

    def test_character_diff_item(self, mock_ns, char_data):
        """ test character_diff() """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        cname = char_data['name'] + '@' + char_data['realm']
        ccache = {cname: char_data}
        new_data = deepcopy(char_data)
        new_data['items']['shoulder'] = {u'stats': [{u'stat': 59,
                                                     u'amount': 60},
                                                    {u'stat': 32,
                                                     u'amount': 80},
                                                    {u'stat': 5,
                                                     u'amount': 109},
                                                    {u'stat': 7,
                                                     u'amount': 163}],
                                         u'name': u'Mantle of Hooded Nightmares of the Savage',
                                         u'tooltipParams': {},
                                         u'armor': 60,
                                         u'quality': 3,
                                         u'itemLevel': 615,
                                         u'context': u'dungeon-normal',
                                         u'bonusLists': [83],
                                         u'id': 114395,
                                         u'icon': u'inv_cloth_draenordungeon_c_01shoulder'}
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
                    "change items.shoulder.name from Twin-Gaze Spaulders "
                    "to Mantle of Hooded Nightmares of the Savage",
                    "remove items.shoulder.tooltipParams [(u'transmogItem', 31054)]",
                    "change items.shoulder.armor from 71 to 60",
                    "change items.shoulder.quality from 4 to 3",
                    "change items.shoulder.icon from inv_shoulder_cloth_draenorlfr_c_01 "
                    "to inv_cloth_draenordungeon_c_01shoulder",
                    "change items.shoulder.itemLevel from 640 to 615",
                    "change items.shoulder.id from 115997 to 114395",
                    "add items.shoulder.bonusLists [(0, 83)]",
                    ]
        expected_s = "\n".join(sorted(expected))
        assert result == expected_s

    def test_char_has_changes_false(self, mock_ns, char_data):
        """ test character_has_changes() without changes """
        bn, rc, mocklog, s, conn, lcc = mock_ns

        def fix_se(char, no_stat=False):
            return char

        orig_data = char_data
        cname = char_data['name'] + '@' + char_data['realm']
        ccache = {cname: orig_data}
        new_data = deepcopy(orig_data)
        s.character_cache = ccache
        with patch('autosimulationcraft.autosimulationcraft.'
                   'AutoSimulationCraft.fix_char_for_diff') as mock_fix_char:
            mock_fix_char.side_effect = fix_se
            result = s.character_has_changes(cname, new_data)
        assert result is None

    def test_char_has_changes_new(self, mock_ns, char_data):
        """ test character_has_changes() on never-before-seen character """
        bn, rc, mocklog, s, conn, lcc = mock_ns

        def fix_se(char, no_stat=False):
            return char

        orig_data = char_data
        cname = char_data['name'] + '@' + char_data['realm']
        ccache = {}
        new_data = deepcopy(orig_data)
        s.character_cache = ccache
        with patch('autosimulationcraft.autosimulationcraft.'
                   'AutoSimulationCraft.fix_char_for_diff') as mock_fix_char:
            mock_fix_char.side_effect = fix_se
            result = s.character_has_changes(cname, new_data)
        assert result == "Character not in cache (has not been seen before)."

    def test_fix_char_for_diff(self, mock_ns, char_data):
        bn, rc, mocklog, s, conn, lcc = mock_ns
        sample_data = {'foo': 'bar', 'baz': 'blam'}
        result = s.fix_char_for_diff(sample_data)
        assert result == {'foo': 'bar', 'baz': 'blam'}

    def test_fix_char_for_diff_profs(self, mock_ns, char_data):
        bn, rc, mocklog, s, conn, lcc = mock_ns
        assert 'professions' in char_data
        result = s.fix_char_for_diff(char_data)
        assert 'professions' not in result

    def test_fix_char_for_diff_kills(self, mock_ns, char_data):
        bn, rc, mocklog, s, conn, lcc = mock_ns
        assert 'totalHonorableKills' in char_data
        result = s.fix_char_for_diff(char_data)
        assert 'totalHonorableKills' not in result

    def test_fix_char_for_diff_no_stats(self, mock_ns, char_data):
        bn, rc, mocklog, s, conn, lcc = mock_ns
        assert 'stats' in char_data
        result = s.fix_char_for_diff(char_data, no_stat=True)
        assert 'stats' not in result

    def test_do_character_no_simc(self, mock_ns):
        """ test do_character() with SIMC_PATH non-existant """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_name = 'cname@rname'
        c_settings = {
            'realm': 'rname',
            'name': 'cname',
            'email': ['foo@example.com']}
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
        with patch('autosimulationcraft.autosimulationcraft.'
                   'os.path.exists') as mock_ope, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'open', create=True) as mocko, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'os.chdir') as mock_chdir, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.now') as mock_dtnow, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'subprocess.check_output') as mock_subp, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.send_char_email') as mock_sce:
            mock_ope.side_effect = mock_ope_se
            mock_dtnow.side_effect = mock_dtnow_se
            s.settings = settings
            s.do_character(c_name, c_settings, c_diff)
        assert mock_ope.call_args_list == [call('/path/to/simc')]
        assert mocko.mock_calls == []
        assert mock_chdir.call_args_list == []
        assert mock_subp.call_args_list == []
        assert mock_sce.call_args_list == []
        assert mocklog.error.call_args_list == [
            call('ERROR: simc path /path/to/simc does not exist')]

    def test_do_character(self, mock_ns):
        """ test do_character() in normal case """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_name = 'cname@rname'
        c_settings = {
            'realm': 'rname',
            'name': 'cname',
            'email': ['foo@example.com']}
        c_diff = 'diffcontent'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])

        def mock_ope_se(p):
            return True
        with patch('autosimulationcraft.autosimulationcraft.'
                   'os.path.exists') as mock_ope, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'open', create=True) as mocko, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'os.chdir') as mock_chdir, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.now') as mock_dtnow, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'subprocess.check_output') as mock_subp, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.options_for_char') as mock_ofc, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.send_char_email') as mock_sce:
            mock_ope.side_effect = mock_ope_se
            mock_ofc.return_value = 'foo\n'
            mock_dtnow.side_effect = [
                datetime.datetime(
                    2014, 1, 1, 0, 0, 0), datetime.datetime(
                    2014, 1, 1, 1, 2, 3)]
            mock_subp.return_value = 'subprocessoutput'
            s.settings = settings
            s.do_character(c_name, c_settings, c_diff)
        assert mock_ope.call_args_list == [
            call('/path/to/simc'),
            call('/home/user/.autosimulationcraft/cname@rname.html')]
        assert mocko.mock_calls == [call('/home/user/.autosimulationcraft/cname@rname.simc', 'w'),
                                    call().__enter__(),
                                    call().__enter__().write(
                                        '"armory=us,rname,cname"\n'),
                                    call().__enter__().write(
                                        'foo\n'),
                                    call().__enter__().write(
                                        'html=cname@rname.html'),
                                    call().__exit__(None, None, None)]
        assert mock_ofc.call_args_list == [call(c_settings)]
        assert mock_chdir.call_args_list == [
            call('/home/user/.autosimulationcraft')]
        fpath = '/home/user/.autosimulationcraft/cname@rname.simc'
        assert mock_subp.call_args_list == [call(['/path/to/simc',
                                                  fpath],
                                                 stderr=subprocess.STDOUT)]
        assert mock_sce.call_args_list == [call('cname@rname',
                                                {'realm': 'rname',
                                                 'name': 'cname',
                                                 'email': ['foo@example.com']},
                                                'diffcontent',
                                                '/home/user/.autosimulationcraft/cname@rname.html',
                                                datetime.timedelta(
                                                    seconds=3723),
                                                'subprocessoutput')]
        assert mocklog.error.call_args_list == []

    def test_do_character_simc_error(self, mock_ns):
        """ test do_character() with simc exiting non-0 """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_name = 'cname@rname'
        c_settings = {
            'realm': 'rname',
            'name': 'cname',
            'email': ['foo@example.com']}
        c_diff = 'diffcontent'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])

        def mock_ope_se(p):
            return True

        with patch('autosimulationcraft.autosimulationcraft.'
                   'os.path.exists') as mock_ope, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'open', create=True) as mocko, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'os.chdir') as mock_chdir, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.now') as mock_dtnow, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'subprocess.check_output') as mock_subp, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.options_for_char') as mock_ofc, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.send_char_email') as mock_sce:
            mock_ope.side_effect = mock_ope_se
            mock_ofc.return_value = 'foo\n'
            mock_dtnow.side_effect = [
                datetime.datetime(
                    2014, 1, 1, 0, 0, 0), datetime.datetime(
                    2014, 1, 1, 1, 2, 3)]
            mock_subp.side_effect = subprocess.CalledProcessError(
                1,
                'command',
                'erroroutput')
            s.settings = settings
            s.do_character(c_name, c_settings, c_diff)
        assert mock_ope.call_args_list == [call('/path/to/simc')]
        assert mocko.mock_calls == [call('/home/user/.autosimulationcraft/cname@rname.simc', 'w'),
                                    call().__enter__(),
                                    call().__enter__().write(
                                        '"armory=us,rname,cname"\n'),
                                    call().__enter__().write(
                                        'foo\n'),
                                    call().__enter__().write(
                                        'html=cname@rname.html'),
                                    call().__exit__(None, None, None)]
        assert mock_chdir.call_args_list == [
            call('/home/user/.autosimulationcraft')]
        fpath = '/home/user/.autosimulationcraft/cname@rname.simc'
        assert mock_subp.call_args_list == [call(['/path/to/simc',
                                                  fpath],
                                                 stderr=subprocess.STDOUT)]
        assert mock_sce.call_args_list == []
        assert mocklog.error.call_args_list == [call('Error running simc!')]

    def test_do_character_no_html(self, mock_ns):
        """ do_character() - simc runs but HTML not created """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_name = 'cname@rname'
        c_settings = {
            'realm': 'rname',
            'name': 'cname',
            'email': ['foo@example.com']}
        c_diff = 'diffcontent'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])

        def mock_ope_se(p):
            if p == '/home/user/.autosimulationcraft/cname@rname.html':
                return False
            return True

        with patch('autosimulationcraft.autosimulationcraft.'
                   'os.path.exists') as mock_ope, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'open', create=True) as mocko, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'os.chdir') as mock_chdir, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.now') as mock_dtnow, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'subprocess.check_output') as mock_subp, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.options_for_char') as mock_ofc, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.send_char_email') as mock_sce:
            mock_ope.side_effect = mock_ope_se
            mock_ofc.return_value = 'foo\n'
            mock_dtnow.side_effect = [
                datetime.datetime(
                    2014, 1, 1, 0, 0, 0), datetime.datetime(
                    2014, 1, 1, 1, 2, 3)]
            mock_subp.return_value = 'simcoutput'
            s.settings = settings
            s.do_character(c_name, c_settings, c_diff)
        assert mock_ope.call_args_list == [
            call('/path/to/simc'),
            call('/home/user/.autosimulationcraft/cname@rname.html')]
        assert mocko.mock_calls == [call('/home/user/.autosimulationcraft/cname@rname.simc', 'w'),
                                    call().__enter__(),
                                    call().__enter__().write(
                                        '"armory=us,rname,cname"\n'),
                                    call().__enter__().write(
                                        'foo\n'),
                                    call().__enter__().write(
                                        'html=cname@rname.html'),
                                    call().__exit__(None, None, None)]
        assert mock_chdir.call_args_list == [
            call('/home/user/.autosimulationcraft')]
        fpath = '/home/user/.autosimulationcraft/cname@rname.simc'
        assert mock_subp.call_args_list == [call(['/path/to/simc',
                                                  fpath],
                                                 stderr=subprocess.STDOUT)]
        assert mock_sce.call_args_list == []
        assert mocklog.error.call_args_list == [
            call('ERROR: simc finished but HTML file not found on disk.')]

    def test_options_for_char_none(self, mock_ns):
        """ test options_for_char() with none """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_settings = {
            'realm': 'rname',
            'name': 'cname',
            'email': ['foo@example.com']}
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])

        s.settings = settings
        res = s.options_for_char(c_settings)
        assert res == ''

    def test_options_for_char_global(self, mock_ns):
        """ test options_for_char() with only global options """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_settings = {
            'realm': 'rname',
            'name': 'cname',
            'email': ['foo@example.com']}
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        setattr(settings, 'GLOBAL_OPTIONS', {'foo': 'bar', 'baz': 'blam'})

        s.settings = settings
        res = s.options_for_char(c_settings)
        assert res == 'baz=blam\nfoo=bar\n'

    def test_options_for_char_charonly(self, mock_ns):
        """ test options_for_char() with only per-char options """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_settings = {
            'realm': 'rname',
            'name': 'cname',
            'email': ['foo@example.com'],
            'options': {'foo': 'bar', 'baz': 'blam'},
        }
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        s.settings = settings
        res = s.options_for_char(c_settings)
        assert res == 'baz=blam\nfoo=bar\n'

    def test_options_for_char_merge(self, mock_ns):
        """ test options_for_char() with non-conflicting char and global options """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_settings = {
            'realm': 'rname',
            'name': 'cname',
            'email': ['foo@example.com'],
            'options': {'c1': 'c1val', 'c2': 'c2val'},
        }
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        setattr(settings, 'GLOBAL_OPTIONS', {'g1': 'g1val', 'g2': 'g2val'})
        s.settings = settings
        res = s.options_for_char(c_settings)
        assert res == 'c1=c1val\nc2=c2val\ng1=g1val\ng2=g2val\n'

    def test_options_for_char_override(self, mock_ns):
        """ test options_for_char() with char options overriding global """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_settings = {
            'realm': 'rname',
            'name': 'cname',
            'email': ['foo@example.com'],
            'options': {'c1': 'c1val', 'c2': 'c2val', 'zzz': 'charval'},
        }
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        setattr(settings, 'GLOBAL_OPTIONS', {'g1': 'g1val', 'g2': 'g2val', 'zzz': 'globalval'})
        s.settings = settings
        res = s.options_for_char(c_settings)
        assert res == 'c1=c1val\nc2=c2val\ng1=g1val\ng2=g2val\nzzz=charval\n'

    def test_send_char_email(self, mock_ns):
        """ test send_char_email() in normal case """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        c_settings = {
            'realm': 'rname',
            'name': 'cname',
            'email': ['foo@example.com']}
        c_name = 'cname@rname'
        c_diff = 'diffcontent'
        html_path = '/path/to/output.html'
        duration = datetime.timedelta(seconds=3723)  # 1h 2m 3s
        output = 'simc_output_string'
        subj = 'SimulationCraft report for cname@rname'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        with patch('autosimulationcraft.autosimulationcraft.'
                   'AutoSimulationCraft.send_gmail') as mock_gmail, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.format_message', spec_set=MIMEMultipart) as mock_format, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.send_local') as mock_local, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'platform.node') as mock_node, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'getpass.getuser') as mock_user:
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
        subj = 'SimulationCraft report for cname@rname'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        with patch('autosimulationcraft.autosimulationcraft.'
                   'AutoSimulationCraft.send_gmail') as mock_gmail, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.format_message', spec_set=MIMEMultipart) as mock_format, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.send_local') as mock_local, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'platform.node') as mock_node, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'getpass.getuser') as mock_user:
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

    def test_send_char_email_gmailnone(self, mock_ns):
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
        subj = 'SimulationCraft report for cname@rname'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        setattr(settings, 'GMAIL_USERNAME', None)
        setattr(settings, 'GMAIL_PASSWORD', 'gmailpass')
        with patch('autosimulationcraft.autosimulationcraft.'
                   'AutoSimulationCraft.send_gmail') as mock_gmail, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.format_message', spec_set=MIMEMultipart) as mock_format, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.send_local') as mock_local, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'platform.node') as mock_node, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'getpass.getuser') as mock_user:
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
        subj = 'SimulationCraft report for cname@rname'
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        setattr(settings, 'GMAIL_USERNAME', 'gmailuser')
        setattr(settings, 'GMAIL_PASSWORD', 'gmailpass')
        with patch('autosimulationcraft.autosimulationcraft.'
                   'AutoSimulationCraft.send_gmail') as mock_gmail, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.format_message', spec_set=MIMEMultipart) as mock_format, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.send_local') as mock_local, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'platform.node') as mock_node, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'getpass.getuser') as mock_user:
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
        settings = Container()
        setattr(settings, 'SIMC_PATH', '/path/to/simc')
        setattr(settings, 'CHARACTERS', [c_settings])
        with patch('autosimulationcraft.autosimulationcraft.'
                   'AutoSimulationCraft.send_gmail') as mock_gmail, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.format_message', spec_set=MIMEMultipart) as mock_format, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.send_local') as mock_local, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'platform.node') as mock_node, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'getpass.getuser') as mock_user:
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
        assert mocklog.info.call_args_list == [
            call("Sending email for character cname@rname to foo@example.com")]
        assert mocklog.warning.call_args_list == [
            call("DRY RUN - not actually sending email")]
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
        expected += 'This run was done on nodename at 2014-01-01 00:00:00 by '
        expected += 'autosimulationcraft.py va.b.c'
        with patch('autosimulationcraft.autosimulationcraft.'
                   'platform.node') as mock_node, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'AutoSimulationCraft.now') as mock_now, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'open', create=True) as mock_open, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'make_msgid') as mock_msgid, \
                patch('autosimulationcraft.autosimulationcraft.'
                      'formatdate') as mock_date:
            mock_msgid.return_value = 'mymessageid'
            mock_date.return_value = 'mydate'
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
        assert res['From'] == 'AutoSimulationCraft <{f}>'.format(f=from_addr)
        assert res['Date'] == 'mydate'
        assert res['Message-Id'] == 'mymessageid'
        assert res._payload[0]._payload == expected
        assert b64decode(res._payload[1]._payload) == htmlcontent
        assert (
            'Content-Disposition',
            'attachment; filename="cname@rname.html"') in res._payload[1]._headers
        assert b64decode(res._payload[2]._payload) == output
        assert (
            'Content-Disposition',
            'attachment; filename="cname@rname_simc_output.txt"') in res._payload[2]._headers
        assert len(res._payload) == 3
        file_handle = mock_open.return_value.__enter__.return_value
        assert mock_open.call_args_list == [call('/path/to/file.html', 'r')]
        assert file_handle.read.call_count == 1
        assert mock_date.call_args_list == [call(localtime=True)]
        assert mock_msgid.call_args_list == [call()]

    def test_send_local(self, mock_ns):
        """ send_local() test """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        with patch('autosimulationcraft.autosimulationcraft.'
                   'smtplib.SMTP', autospec=True) as mock_smtp:
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
        with patch('autosimulationcraft.autosimulationcraft.'
                   'smtplib.SMTP', autospec=True) as mock_smtp:
            s.settings = settings
            s.send_gmail('from', 'to', 'msg')
        assert mock_smtp.mock_calls == [call('smtp.gmail.com:587'),
                                        call().starttls(),
                                        call().login(
            'myusername',
            'mypassword'),
            call().sendmail('from', ['to'], 'msg'),
            call().quit()
        ]

    def test_make_char_name(self, mock_ns):
        """ make_character_name() tests """
        bn, rc, mocklog, s, conn, lcc = mock_ns
        assert s.make_character_name('n', 'r') == 'n@r'
        assert s.make_character_name('MyName', 'MyRealm') == 'MyName@MyRealm'
        assert s.make_character_name(
            'sómÊñámé',
            'Area 52') == 'sómÊñámé@Area52'

    @freeze_time("2014-01-01 01:02:03")
    def test_now(self, mock_ns):
        bn, rc, mocklog, s, conn, lcc = mock_ns
        result = s.now()
        assert result == datetime.datetime(2014, 1, 1, 1, 2, 3)
