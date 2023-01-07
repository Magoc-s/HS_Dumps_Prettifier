import enum
from typing import Union
from src.helpers import is_float, is_string


class LuaLineTypes(enum.Enum):
    """
    Type enum for the LuaLineInterpretor tokens.

    Specifies all the line types we expect to see in the Endo-formatted High Seas Dumps file.

    VAR_ASSIGN is when we have a variable assignment with a literal, i.e.: `my_var = 1.23`
    VAR_TABLE_ASSIGN is when we have a variable assignment that is creating a table, i.e.:
        `my_table =
            {
                ...
            }`
    VAR_TABLE_OPEN is the single `{` in the second line of the previous example
    VAR_TABLE_CLOSE is the single '}' on the last line of the previous example
    VAR_LITERAL is when there is a literal on its own on a line, i.e.: `1.23` (usually only seen in literal tables)
    VAR_IMMEDIATE_TABLE_OPEN_CLOSE is when a table is empty, i.e.:
        `my_table =
         {}`
    COMMENT is when a line starts with '--', i.e. a lua comment
    """
    VAR_ASSIGN = enum.auto(),
    VAR_TABLE_ASSIGN = enum.auto(),
    VAR_TABLE_OPEN = enum.auto(),
    VAR_TABLE_CLOSE = enum.auto(),
    VAR_LITERAL = enum.auto(),
    VAR_IMMEDIATE_TABLE_OPEN_CLOSE = enum.auto(),
    COMMENT = enum.auto(),


class LuaLineInterpretor:
    """
    Turns a string token of a lua line from the dumps file into a proper token with a type from the
    LuaLineTypes enum.

    Exposes get_type() and get_line() methods.
    """
    def __init__(self, line: str) -> None:
        """
        Takes a line and parses it through a rules ladder to assign it the most correct LuaLineTypes type,
        then extracts values for other variables necessary for the given type.

        The object has the following instance params when self._type is:
        VAR_ASSIGN:
            self.var_name: the name of the variable being assigned too (i.e. LHS of the '=' symbol)
            self.assign_value: the value being assigned to the variable (i.e. RHS of the '=' symbol)
            self.assign_type: the callable type class for the type of the assign_value (Union[int, float, str, None])

        VAR_TABLE_ASSIGN:
            self.table_name: the name of the table being created

        VAR_LITERAL:
            self.literal_value: the value of the literal on this line,
            self.literal_type: the type of the literal, in callable class form. Same as above.

        COMMENT:
            self.comment: the comment string

        :param line: a string token line from the HS dumps file
        """
        self._line = line.strip()
        # find type of line.
        # In the HS_Dumps.lua file, there are
        self._type: Union[None, LuaLineTypes] = None
        if self._line.startswith("--"):
            self._type = LuaLineTypes.COMMENT
        elif self._line == "{}":
            self._type = LuaLineTypes.VAR_IMMEDIATE_TABLE_OPEN_CLOSE
        elif self._line.endswith(" =") or self._line.endswith("= {"):
            self._type = LuaLineTypes.VAR_TABLE_ASSIGN
        elif self._line == "{":
            self._type = LuaLineTypes.VAR_TABLE_OPEN
        elif self._line == "}," or self._line == "}":
            self._type = LuaLineTypes.VAR_TABLE_CLOSE
        elif "=" in self._line and not self._line.endswith("="):
            self._type = LuaLineTypes.VAR_ASSIGN
        elif self._is_literal():
            self._type = LuaLineTypes.VAR_LITERAL
        # extract relevant information from raw lua string
        if self._type == LuaLineTypes.VAR_ASSIGN:
            self.var_name = self._line.split("=")[0].strip()
            self.assign_value = self._line.split("=")[1].strip()
            self.assign_type: Union[callable, None] = None
            # strip ending comma if its in a table
            if self.assign_value.endswith(","):
                self.assign_value = str(self.assign_value[:len(self.assign_value) - 1])
            # set assign type for relevant details later
            if is_string(self.assign_value):
                self.assign_type = str
            elif self.assign_value.isdecimal():
                self.assign_type = int
            elif is_float(self.assign_value):
                self.assign_type = float
            else:
                self.assign_type = str

        elif self._type == LuaLineTypes.VAR_TABLE_ASSIGN:
            self.table_name = self._line.split("=")[0].strip()
        elif self._type == LuaLineTypes.VAR_LITERAL:
            self.literal_value = self._line.replace(",", "")
            if is_string(self.literal_value):
                self.literal_type = str
            elif self.literal_value.isdecimal():
                self.literal_type = int
            elif is_float(self.literal_value):
                self.literal_type = float
            else:
                self.literal_type = str

        elif self._type == LuaLineTypes.COMMENT:
            self.comment = self._line.replace("--", "", 1)

    def _is_literal(self) -> bool:
        """
        Determine if the given string line token is a literal value or not, by running it through the
        various helpers to determine type.

        Literal value properties are things like:
        - String starts and ends with quotes (string literal)
        - string is entirely numeric characters (int literal)
        - string is entirely numeric characters, '-' and '.' (float literal)

        :return: true if it exhibits properties of a literal value
        """
        if is_string(self._line):
            return True
        try:
            if self._line.endswith(","):
                float(self._line.replace(",", ""))
                return True
            else:
                float(self._line.replace(",", ""))
                return True
        except ValueError:
            pass

    def get_type(self) -> LuaLineTypes:
        """
        The type of this LuaLineInterpretor token cannot change once it is instantiated.
        :return: the self._type value, which is the LuaLineTypes specifier based on the line provided on instantiation.
        """
        return self._type

    def get_line(self) -> str:
        """
        :return: The string token the object was instantiated with.
        """
        return self._line
