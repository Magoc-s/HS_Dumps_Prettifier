import os
import sys
import time
import shutil
import yaml
import re
from src.search import SEARCH_MAPPING
from src.dumblua import LuaLineTypes, LuaLineInterpretor
from src.helpers import write_subkeys

# Use this lib if desired to decode the b64encoded functions
import base64

# DEBUG = [0|1]
# If set to 1, will print its path through the nesting as it parses the file
# was used mainly to debug the literal tables implementation as this routinely broke the nesting stack
DEBUG = 0


class DumpLoader:
    """
    Will load a High Seas dumps file and parse the lua syntax tables into a Python dict

    Exposes several functions to save the python dictionary as yaml file(s).
    """
    def __init__(self, file_name: str) -> None:
        """
        Tokenises and parses the dumps file, turning lines into `src.dumblua.LuaLineInterpretor` tokens
        for interpreting.

        Splits standard object dumps and script dumps into separate tables (self.tables and self.script_tables)
        respectively.

        A file with non-Endo formatting will most probably crash this.

        :param file_name: the name of the High Seas Dumps file (in the format provided by Endo)
        """
        self._file_name: str = file_name
        with open(self._file_name, 'r') as h:
            self._file_contents: str = h.read()
        self.b64_funcs = []
        # Nuke out the multiline b64 encoded functions which break the tokeniser
        self.extract_b64_encoded_funcs()
        # Split into string tokens by newlines
        self._file_lines = self._file_contents.split("\n")
        self.categories = []

        self.tables = {}
        self.scripts = []
        self.script_tables = {}
        for line in self._file_lines:
            # Extract the category names and script names by using the section header and footer formatters
            if line.startswith("-- ========== BEGIN"):
                self.categories.append(line.replace("-- ========== BEGIN", "").replace("DUMP ==========", "").strip())
            elif line.startswith("-- =*=*=*=*=*") and line.endswith(":: BEGIN SCRIPT DUMP *=*=*=*=*="):
                self.scripts.append(
                    line.replace("-- =*=*=*=*=*", "").replace(":: BEGIN SCRIPT DUMP *=*=*=*=*=", "").strip()
                )
        for cat in self.categories:
            # create a table for each category, extracting the category contents in string form from the dumps file
            self.tables[cat] = {}
            _cat_content = self._file_contents.split(f"-- ========== BEGIN {cat} DUMP ==========")[1] \
                .split(f"-- ==========  END {cat} DUMP  ==========")[0]
            # Tokenise each line of the category contents via the `src.dumblua.LuaLineInterpretor` tokeniser
            _interpreted_lines: list[LuaLineInterpretor] = []
            for line in _cat_content.split("\n"):
                _interpreted_lines.append(LuaLineInterpretor(line))
            _to_add = {}
            # the _open_table var is a list of table names, used to keep track of the amount of nesting
            # through the document. We traverse the list to navigate the intermediate py dict correctly for assigning
            # values. FIFO stack style.
            _open_table = [] # Stack of nested tables
            # Now iterate the line tokens to keep track of the nesting and create sub-dicts or key-value pairs
            # where necessary, by looking at the type of the token (specified by `src.dumblua.LuaLineTypes: Enum`)
            for lualine in _interpreted_lines:
                if lualine.get_type() == LuaLineTypes.VAR_TABLE_ASSIGN:
                    _local_table = _to_add
                    # Traverse the table stack to navigate the intermediate dict to end up at the right endpoint
                    # then create a new table with the given name
                    for open_tab in _open_table:
                        _local_table = _local_table[open_tab]

                    _open_table.append(lualine.table_name)
                    _local_table[str(_open_table[-1])] = {}
                # A token whose contents is a single '{' is a superfluous token, as we've already created a table with
                # the previously specified name, and the non-script section of the HS Dumps file doesn't have
                # literal tables. See script loop for behaviour where literal tables are present.
                elif lualine.get_type() == LuaLineTypes.VAR_TABLE_OPEN:
                    pass
                # Pop off the stack FIFO style. Go up one layer of nesting/indentation
                elif lualine.get_type() == LuaLineTypes.VAR_TABLE_CLOSE:
                    _open_table.pop()
                # Add a key value pair for the variable and value assigned here, casting to the correct primative type
                # as well. (str, int, float)
                elif lualine.get_type() == LuaLineTypes.VAR_ASSIGN:
                    _local_table = _to_add
                    for open_tab in _open_table:
                        _local_table = _local_table[open_tab]
                    if "\"" in lualine.assign_value:
                        lualine.assign_value = lualine.assign_value.replace("\"", "")
                    if "\\\"" in lualine.assign_value:
                        lualine.assign_value = lualine.assign_value.replace("\\\"", "")
                    _local_table[lualine.var_name] = lualine.assign_type(lualine.assign_value)
            # Add the full category table to our main tables dict
            self.tables[cat] = _to_add

        for script in self.scripts:
            # Grab a name for the file from the script name
            # (pulled from the "-- =*=*=*=*=* {script} :: BEGIN SCRIPT DUMP *=*=*=*=*=" string)
            script_obj_name = script
            # If script follows the naming standard `Minigun [minigun]`, use the [object] name
            if "[" in script and "]" in script:
                script_obj_name = script.split("[")[1].split("]")[0].strip()
                # The hardpoint has a blank object name for what the fuck ever, so just reset to scriptobj name
                if script_obj_name == "":
                    script_obj_name = script
            self.script_tables[script_obj_name] = {}
            _script_content = self._file_contents.split(f"-- =*=*=*=*=* {script} :: BEGIN SCRIPT DUMP *=*=*=*=*=")[1] \
                .split(f"-- =*=*=*=*=* {script} :: END SCRIPT DUMP *=*=*=*=*=")[0]
            _interpreted_lines: list[LuaLineInterpretor] = []
            for line in _script_content.split("\n"):
                _interpreted_lines.append(LuaLineInterpretor(line))
            # 'Literal tables' is how I handle Lua's table literals in yaml form.
            # I.e.
            # ```lua
            # test_table = {
            #   {
            #       obj1 = 1,
            #       obj2 = 2
            #   }
            # }
            # ```
            # YAML doesn't support literal tables like this without giving them a key name (just like py doesn't
            # support having nested dicts without a key).
            # To get around this, I use a "literal_table_{_literal_table_counter}" key to house the literal tables
            # that the scripts use
            _literal_table_counter = 0
            _to_add = {}
            # the _open_table var is a list of table names, used to keep track of the amount of nesting
            # through the document. We traverse the list to navigate the intermediate py dict correctly for assigning
            # values. FIFO stack style.
            _open_table = [] # Stack of nested tables
            _last_line = None
            if DEBUG == 1:
                print(script)
            for lualine in _interpreted_lines:
                if lualine.get_type() == LuaLineTypes.VAR_TABLE_ASSIGN:
                    _local_table = _to_add
                    for open_tab in _open_table:
                        _local_table = _local_table[open_tab]

                    _open_table.append(lualine.table_name)
                    _local_table[str(_open_table[-1])] = {}
                    if DEBUG == 1:
                        print("OPEN", _open_table[-1])
                # Some tables are defined but empty in the lua dump,
                # i.e.
                # table1 =
                # {}
                # So we need to handle the immediate open then close behaviour, where we've appended
                # the table name on the first line, so now we pop it on this line.
                # Good thing code style choices means the line `table1 = {}` doesn't exist in this doc!
                elif lualine.get_type() == LuaLineTypes.VAR_IMMEDIATE_TABLE_OPEN_CLOSE:
                    if DEBUG == 1:
                        print("CLOSE", _open_table[-1])
                    _open_table.pop()
                elif lualine.get_type() == LuaLineTypes.VAR_TABLE_OPEN:
                    # Catch nested literal tables without a var name, see _literal_table_counter comment
                    if _last_line.get_type() == LuaLineTypes.VAR_TABLE_OPEN or \
                        _last_line.get_type() == LuaLineTypes.VAR_TABLE_CLOSE or \
                            (_last_line.get_type() == LuaLineTypes.VAR_TABLE_ASSIGN and
                             _last_line.get_line().endswith("{")):

                        _local_table = _to_add
                        for open_tab in _open_table:
                            _local_table = _local_table[open_tab]

                        literal_table_name = f"literal_table_{_literal_table_counter}"
                        _literal_table_counter += 1
                        _open_table.append(literal_table_name)
                        _local_table[str(_open_table[-1])] = {}
                        if DEBUG == 1:
                            print("LITERAL OPEN", _open_table[-1])
                # FO part of the stack. We're going up one level of nesting because we hit a '}' symbol
                # so pop the table name from the stack
                elif lualine.get_type() == LuaLineTypes.VAR_TABLE_CLOSE:
                    if DEBUG == 1:
                        print("CLOSE", _open_table[-1])
                    _open_table.pop()
                # A variable assignment line, so add the name and var to the intermediate dict, casting the value
                # to the correct primative type (int, float, str)
                elif lualine.get_type() == LuaLineTypes.VAR_ASSIGN:
                    _local_table = _to_add
                    for open_tab in _open_table:
                        _local_table = _local_table[open_tab]
                    if "\"" in lualine.assign_value:
                        lualine.assign_value = lualine.assign_value.replace("\"", "")
                    if "\\\"" in lualine.assign_value:
                        lualine.assign_value = lualine.assign_value.replace("\\\"", "")
                    _local_table[lualine.var_name] = lualine.assign_type(lualine.assign_value)

                _last_line = lualine

            self.script_tables[script_obj_name] = _to_add

    def extract_b64_encoded_funcs(self) -> None:
        """
        The High Seas Script Dumps have a bunch of base64 encoded script functions included in them,
        which includes large blocks of base64 text across multiple lines that are irrelevant to our
        purposes, so we replace the entire b64encoded block with a placeholder that indicates this
        var was a b64 encoded function.

        If necessary in the future, we can create a map of the decoded function strings and put a pointer
        to the decoded string.

        :return: None
        """
        self._file_contents = re.sub(
            r"loadstring\(Base64dec\(\[\[\s(.+\n)+]]\n*\)\)",
            "%b64_encoded_function%",
            self._file_contents
        )
        # for match in _matches:
        #     self._file_contents = self._file_contents.replace(match, "$$b64_encoded_function$$")

    def write_to_file(self, file_name: str) -> None:
        """
        Writes the main `complete_dump.yml` (this name is specified by the @file_name param) file.

        Performs a simply yaml safe dump. If you want to adjust what directory this file is written too,
        you must call `os.chdir()` first.

        :param file_name: The filename for the big yaml file that contains all the parsed keys.
        :return: None
        """
        with open(file_name, 'w') as h:
            h.write(yaml.safe_dump(self.tables, sort_keys=False))
            h.write(yaml.safe_dump(self.script_tables, sort_keys=False))

    def write_to_files(self, folder_name: str) -> None:
        """
        Writes the collection of files for each individual material, device, weapon and projectile for ease of reading.

        Uses the maps in `src/search.py` to only write the desired variables and values into the files.

        :param folder_name: the name of the output directory. WARNING: if this dir already exists, it will be deleted
        in its entirety before being recreated.
        :return: None
        """
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
        os.mkdir(folder_name)
        os.chdir(folder_name)

        literal = "MATERIALS"
        _mats = self.tables[literal]["Materials"]
        _map = SEARCH_MAPPING[literal]
        os.mkdir(literal)
        os.chdir(literal)
        write_subkeys(_mats, _map)

        literal = "PROJECTILES"
        _projs = self.tables[literal]["Projectiles"]
        _map = SEARCH_MAPPING[literal]
        os.mkdir(literal)
        os.chdir(literal)
        write_subkeys(_projs, _map)

        literal = "DEVICES"
        _devs = self.tables[literal]["Devices"]
        _map = SEARCH_MAPPING[literal]
        os.mkdir(literal)
        os.chdir(literal)
        write_subkeys(_devs, _map)

        literal = "WEAPONS"
        _devs = self.tables[literal]["Weapons"]
        _map = SEARCH_MAPPING[literal]
        os.mkdir(literal)
        os.chdir(literal)
        write_subkeys(_devs, _map)

        literal = "SCRIPTED"
        os.mkdir(literal)
        os.chdir(literal)
        _map = SEARCH_MAPPING[literal]
        _scripts = self.script_tables
        write_subkeys(_scripts, _map)


def main():
    loader = DumpLoader(sys.argv[1])
    loader.write_to_files(sys.argv[2])
    loader.write_to_file("complete_dump.yml")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} dump_filename output_directory")
        print(
            "WARNING: will first delete the given output directory if it already exists, so give a unique folder name!"
        )
        sys.exit(1)
    else:
        start = time.perf_counter()
        main()
        end = time.perf_counter()
        ms = (end - start)
        print(f"Finished in {ms:.03f} seconds.")
