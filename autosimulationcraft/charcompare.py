import json
from tempfile import mkstemp
import subprocess
import os
from distutils.spawn import find_executable

class LuaTable(object):

    """
    Class to handle converting lua tables to JSON, and then parsing the JSON.

    Used to pull data from Warcraft SavedVariables.
    """

    table_name_re = re.compile(r'^\s*(\S+)\s+=', re.M)

    def __init__(self, table_file_path):
        self.lua_bin = find_executable('lua')
        self.lua_table_path = table_file_path

    def get_data(self):
        pass

    def _get_lua_table(self):
        # get the path to JSON.lua
        # d = pkg_resources.get_distribution('autosimulationcraft')
        # >>> d.location
        # '/home/jantman/GIT/AutoSimulationCraft'
        # something like: pkg_resources.resource_filename('autosimulationcraft', 'data/JSON.lua')
        # read in the lua table
        with open(self.lua_path, 'r') as fh:
            lua_table = fh.read()
        lua_table_name = self.table_name_re.match(lua_table).group(1)

        fd, table_path = mkstemp(suffix='.lua')
        os.write(fd, lua_table)
        os.close(fd)

        # the lua script to convert it to JSON; we need to include this in our package
        script = """foo = (loadfile "{fname}")()
        JSON = (loadfile "JSON.lua")() -- one-time load of the routines
        
        local raw_json_text    = JSON:encode({dbname})
        print(raw_json_text)
        """.format(
            fname=table_path,
            dbname=lua_table_name)

        fd, script_path = mkstemp(suffix='.lua')
        os.write(fd, script)
        os.close(fd)

        cmd = subprocess.check_output(['lua', script_path], stderr=subprocess.STDOUT)
        try:
            res = json.loads(cmd)
        except:
            print("ERROR decoding JSON:")
            print(cmd)
            raise SystemExit(1)
        os.unlink(table_path)
        os.unlink(script_path)
        return res
