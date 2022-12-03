"""
Convert YAML file to JSON with identical structure (as a python dict)
Adapted from https://raw.githubusercontent.com/vasil9v/yaml2json.py/c4cfa408bbab4f1a0cd3661d121237030f6bc0ca/yaml2json.py
"""
import sys
import yaml
from hammer.config.yaml2json import convertArrays, compare

def load(f):
    try:
        return (open(f, 'r')).read()
    except IOError:
        return None

def save(f, b): (open(f, 'w')).write(b)

def yaml2json():
    """
    Main function, first arg is the input file, optional second one is the output
    file. If no output file is specified then the output is written to stdout.
    The input file is parsed as YAML and converted to a python dict tree, then
    that tree is converted to the JSON output. There is a check to make sure the
    two dict trees are structurally identical.
    """
    if len(sys.argv) > 1:
        f = sys.argv[1]
        f2 = None
        if len(sys.argv) > 2:
            f2 = sys.argv[2]
        obj = yaml.safe_load(load(f))
        obj = convertArrays(obj)
        outputContent = json.dumps(obj, indent=2)
        obj2 = json.loads(outputContent)
        if not compare(obj, obj2):
            print("error: they dont match structure")
            print("")
            print(str(obj))
            print("")
            print(str(obj2))
        else:
            if f2:
                save(f2, outputContent)
            else:
                print(outputContent)
    else:
        print("usage: yaml2json infile.yaml [outfile.json]")

def main():
    yaml2json()
