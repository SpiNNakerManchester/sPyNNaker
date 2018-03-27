# THIS IS A BASH SCRIPT INTENDED TO BE SOURCED!

# Setup script to define the location of the files and the required binaries

set -a

# Define the location of this library
export NEURAL_MODELLING_DIRS="$( CDPATH= cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# See https://stackoverflow.com/a/246128/301832 for how this works
# and https://stackoverflow.com/a/29835459/301832 for why CDPATH is used
