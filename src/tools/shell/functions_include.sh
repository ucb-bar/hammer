# Misc functions for use in scripts.
# Include them with "source".

# Helper function to join arrays.
# Example: join_by , "${FOO[@]}" #a,b,c
# http://stackoverflow.com/a/17841619
function join_by { local d=$1; shift; echo -n "$1"; shift; printf "%s" "${@/#/$d}"; }
