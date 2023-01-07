Requires >~ Python 3.6

Required python packages:
- PyYaml

USAGE:
```commandline
python3 parse-dump.py <filename of dump file> <output dir name>
```

Included by default, the dump file is named `HS_Dumps.lua`. Typically,
I just use `out` as the output dir name.

Example usage:
```commandline
$ python3 parse-dump.py HS_Dumps.lua out
```

Example:
```commandline
$ python3 parse-dump.py HS_Dumps.lua out
Finished in 1.611 seconds.
$ ls out/
DEVICES  MATERIALS  PROJECTILES  SCRIPTED  WEAPONS  complete_dump.yml
```
