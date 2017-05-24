#!/bin/bash

vroot=`dirname $0`
root="$1"
shift
pattern='*.[ch]'
find $root -name "$pattern" | vera++ --root $vroot --profile spinnaker.tcl --error ${1+"$@"}
exit $?
