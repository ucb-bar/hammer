#!/bin/bash
# Option parser from https://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"
case $key in
    -q)
    QUEUE="$2"
    shift
    shift
    ;;
    -n)
    NUMCPU="$2"
    shift
    shift
    ;;
    -R)
    RESOURCE="$2"
    shift
    shift
    ;;
    -o)
    OUTPUT="$2"
    shift
    shift
    ;;
    -K)
    BLOCKING=1
    shift
    ;;
    *)
    POSITIONAL+=("$1")
    shift
    ;;
esac
done

if [ ! -z "$BLOCKING" ]; then echo "BLOCKING is: $BLOCKING"; fi
if [ ! -z "$QUEUE" ]; then echo "QUEUE is: $QUEUE"; fi
if [ ! -z "$NUMCPU" ]; then echo "NUMCPU is: $NUMCPU"; fi
if [ ! -z "$OUTPUT" ]; then echo "OUTPUT is: $OUTPUT"; fi
if [ ! -z "$RESOURCE" ]; then echo "RESOURCE is: $RESOURCE"; fi
echo "COMMAND is: ${POSITIONAL[@]}"
exec ${POSITIONAL[@]}
