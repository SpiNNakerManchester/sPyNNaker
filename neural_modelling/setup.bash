# THIS IS A BASH SCRIPT INTENDED TO BE SOURCED!

# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Setup script to define the location of the files and the required binaries

set -a

# Define the location of this library
export NEURAL_MODELLING_DIRS="$( CDPATH= cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# See https://stackoverflow.com/a/246128/301832 for how this works
# and https://stackoverflow.com/a/29835459/301832 for why CDPATH is used
