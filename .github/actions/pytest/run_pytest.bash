#!/bin/bash

cmd="pytest $TEST_PKG"
for arg in "$@"; do
	cmd="$cmd --cov $arg"
done
eval $cmd
exit $?
