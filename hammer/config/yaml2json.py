# See LICENSE for licence details.

import os
import sys

# Try to use the system yaml if present, else use the HAMMER-shipped yaml.
try:
    import yaml
except ImportError:
    try:
        sys.path.append("src/tools/pyyaml/lib3")
        import yaml
    except ImportError:
        if "HAMMER_PYYAML_PATH" not in os.environ:
            print("pyyaml not found. Set $HAMMER_PYYAML_PATH to pyyaml/lib3", file=sys.stderr)
            sys.exit(1)
        else:
            sys.path.append(os.environ["HAMMER_PYYAML_PATH"])
            import yaml

import json

def convertArrays(o):
    """
    The YAML parser will take a list of substructures all named with an ints
    and create a python sub dict using those ints as keys. In JSON you can't
    have keys be anything other than strings even though that is valid in a
    python dict. This function recursively converts a python dict tree into
    one where any dicts where all the keys are ints are made into arrays. It
    makes sure the order is preserved.

    Adapted from https://raw.githubusercontent.com/vasil9v/yaml2json.py/c4cfa408bbab4f1a0cd3661d121237030f6bc0ca/yaml2json.py
    """
    if type(o) == list:
        for i in range(len(o)):
            o[i] = convertArrays(o[i])
        return o
    if type(o) == dict:
        allNums = True  # type: bool
        if len(o) == 0:
            # Don't convert anything if the dictionary is empty
            allNums = False
        else:
            # Check if it's the case that each key is an int
            for i in o:
                o[i] = convertArrays(o[i])
                if type(i) != int:
                    allNums = False
        # if so, convert it to an array
        if allNums:
            k = sorted(o.keys())
            arr = []
            for i in k:
                arr.append(o[i])
            return arr
    return o

def compare(o1, o2):
    """
    Recursively compares each item in a python dict tree to make sure they are
    the same.

    Adapted from https://raw.githubusercontent.com/vasil9v/yaml2json.py/c4cfa408bbab4f1a0cd3661d121237030f6bc0ca/yaml2json.py
    """
    if o1 == o2:
        return True # shortcut if they're the same primitive
    if type(o1) != type(o2):
        return False # shortcut if they're not the same type
    if type(o1) == type({}):
        k1 = sorted(o1.keys())
        k2 = sorted(o2.keys())
        if k1 == k2: # make sure the sorted keys of the 2 dicts match
            for i in o1: # recursively compare each sub item
                if not compare(o1[i], o2[i]):
                    return False
        else:
            return False
    if type(o1) == type([]): # compare each item in an array
        if len(o1) != len(o2):
            return False
        for i in range(len(o1)):
            if not compare(o1[i], o2[i]):
                return False
    return (o1 == o2)


def load_yaml(yamlStr: str) -> dict:
    """
    Load a YAML database as JSON.

    The input file is parsed as YAML and converted to a python dict tree, then
    that tree is converted to the JSON output. There is a check to make sure the
    two dict trees are structurally identical.

    :param yamlStr: A string containing the yaml database.
    :return: A dictionary object representing the yaml database.
    """
    obj = convertArrays(yaml.safe_load(yamlStr))
    # Note we are not using HammerJSONEncoder here to avoid a circular dependency, but this should never need have Decimals
    obj2 = json.loads(json.dumps(obj))
    if not compare(obj, obj2):
        raise ValueError("YAML -> JSON structures don't match: %s and %s do not match" % (str(obj), str(obj2)))
    else:
        if obj2 is None:
            # Loading a YAML file with nothing (except comments) can return None.
            return {}
        else:
            assert isinstance(obj2, dict), "Config databases should be a dictionary"
            return obj2
