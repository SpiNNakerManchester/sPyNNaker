# THIS IS A BASH SCRIPT INTENDED TO BE SOURCED!

# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Setup script to define the location of the files and the required binaries

set -a

# Define the location of this library
export NEURAL_MODELLING_DIRS="$( CDPATH= cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# See https://stackoverflow.com/a/246128/301832 for how this works
# and https://stackoverflow.com/a/29835459/301832 for why CDPATH is used
