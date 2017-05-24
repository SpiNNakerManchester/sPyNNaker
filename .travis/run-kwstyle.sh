#!/bin/bash

root=$1
shift
find $root -type f -name '*.[ch]' -print0 | xargs -p0 -n 1 "$@"
