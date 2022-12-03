#  get-config
#
#  Read a config from either the given JSON database (if present) or the HAMMER_DATABASE environment variable.
#
#  See LICENSE for licence details.

# pylint: disable=invalid-name

import argparse
import json
import os
import sys

import hammer.config as hammer_config

def run(args):
    if args.db is None:
        try:
            db_location = os.environ["HAMMER_DATABASE"]
        except KeyError:
            print("No database --db specified and HAMMER_DATABASE is not defined", file=sys.stderr)
            return 1
    else:
        db_location = args.db
    database = hammer_config.HammerDatabase()
    # TODO(edwardw): rethink this hack? This simply treats the entire exported JSON as a "project JSON", which might actually be ok.
    database.update_project([json.load(open(db_location))])
    try:
        print(str(database.get_setting(args.key, args.nullvalue)))
        return 0
    except ValueError as e:
        print("Error: " + e.args[0], file=sys.stderr)
        return 1

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--nullvalue", default="null", required=False,
                        help='Value to print out for nulls. (default: "null")')
    parser.add_argument("-e", "--error-if-missing", action='store_const',
                        const=True, default=False, required=False,
                        help="Error out if the key is missing. (default: false)")
    parser.add_argument('--db', type=str, required=False,
                        help='Path to the JSON database')
    parser.add_argument('key', metavar='KEY', type=str,
                        help='Key to retrieve from the database')

    sys.exit(run(parser.parse_args()))
