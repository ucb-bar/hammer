#!/bin/sh
# Run mypy.sh but sorts and removes duplicates from multiple calls to mypy.

./mypy.sh > _stdout.txt
mypy_status=$?

cat _stdout.txt | sort -u
rm -f _stdout.txt
exit ${mypy_status}
