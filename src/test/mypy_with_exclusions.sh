#!/bin/sh
# Run mypy.sh but sorts and removes duplicates from multiple calls to mypy.
# Pass the technology name as the first argument if you also want to type check the hammer-<tech>-plugin.

./mypy.sh "$@" > _stdout.txt
mypy_status=$?

cat _stdout.txt | sort -u
rm -f _stdout.txt
exit ${mypy_status}
