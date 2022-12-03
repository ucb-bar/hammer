#  Older versions of readlink, like readlink 8.4, don't support multiple
#  arguments to readlink.
#  This script is meant to emulate that behaviour on those systems.
#  Usage:
#  readlink_array foo bar baz == readlink -f foo bar baz
#
#  See LICENSE for licence details.

import sys
import subprocess


def run(args):
    # Pop the script name.
    arg0 = args.pop(0)

    if len(args) == 0:
        print(arg0 + ": missing operand", file=sys.stderr)
        return 1

    for arg in sys.argv:
        # Run 'readlink -f' on each argument, and print the result.
        print(subprocess.check_output(["readlink", "-f", arg]).strip())

    return 0


def main():
    sys.exit(run(sys.argv))
