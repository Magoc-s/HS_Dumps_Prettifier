import yaml
import os


def is_string(line: str) -> bool:
    """
    Determines if the assignment value is a string literal (i.e. starts and ends with double qoutes)
    :param line: A string token line from the dumps file, usually the part after a '=' on a VAR_ASSIGN line
    :return: true if literal value is a string
    """
    return line.startswith("\"") and (line.endswith("\"") or line.endswith("\","))


def is_float(line: str) -> bool:
    """
    Determines if the assignment value is a float literal (i.e. contains only numeric characters, '-' and/or '.')
    :param line: A string token line from the dumps file, usually the part after a '=' on a VAR_ASSIGN line
    :return: true if literal value is a float
    """
    try:
        float(line)
        return True
    except ValueError:
        return False


def write_subkeys(_subdict: dict, searchmap: list) -> None:
    """
    Actually does the file writing for the smaller yaml files for each individual object.

    It expects to be already in the right directory (i.e. `os.chdir()` has been called prior to this)

    Tries to look for a key "SaveName" in the objects to name the file, i.e. device and weapon objects.
    If it cannot find one, instead just names the file whatever that specific dicts key is.

    :param _subdict: the dict in which it will iterate and create files for each sub-key in this dict
    :param searchmap: the map of variables to copy out of the intermediate dict into the yaml file
    (specified in search.py)
    :return: None
    """
    for key in _subdict.keys():
        item = _subdict[key]
        try:
            item_name = item["SaveName"]
        except KeyError:
            item_name = key
        _item_dict = {item_name: {}}
        for search_item in searchmap:
            try:
                _item_dict[item_name][search_item] = item[search_item]
            except KeyError:
                pass
        with open(item_name + ".yml", 'w') as h:
            h.write(yaml.safe_dump(_item_dict))
    os.chdir("..")
