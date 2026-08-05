#!/bin/bash

# Copyright (c) 2026 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This bash assumes that other repositories are installed in parallel
# ruffs SpiNNUtils, spinn_machine and unittests

if [ "$#" -eq  "0" ]
  then
    echo "Using previous setup. Provide an argument to run setup"
    source ../SupportScripts/venv/ruff_runner/bin/activate
else
  python3 -m venv ../SupportScripts/venv/ruff_runner
  source ../SupportScripts/venv/ruff_runner/bin/activate
  python3 -m pip install --upgrade ruff
fi

echo using ruff.toml
ruff check ../SpiNNUtils/spinn_utilities ../SpiNNUtils/unittests \
    ../SpiNNMachine/spinn_machine ../SpiNNMachine/unittests \
    ../SpiNNMan/spinnman ../SpiNNMan/unittests \
    ../SpiNNMan/spinnman_integration_tests ../SpiNNMan/manual_scripts \
    ../PACMAN/pacman ../PACMAN/pacman_test_objects ../PACMAN/unittests \
    ../spalloc/spalloc_client ../spalloc/tests \
     ../SpiNNFrontEndCommon/spinn_front_end_common ../SpiNNFrontEndCommon/unittests \
     ../SpiNNFrontEndCommon/fec_integration_tests \
     spynnaker unittests spynnaker_integration_tests proxy_integration_tests \
     --target-version py310 --config ../SupportScripts/actions/ruff/ruff.toml
echo using ruff_up.toml
ruff check ../SpiNNUtils/spinn_utilities ../SpiNNUtils/unittests \
    ../SpiNNMachine/spinn_machine ../SpiNNMachine/unittests \
    ../SpiNNMan/spinnman ../SpiNNMan/unittests \
    ../SpiNNMan/spinnman_integration_tests ../SpiNNMan/manual_scripts \
    ../PACMAN/pacman ../PACMAN/pacman_test_objects ../PACMAN/unittests \
    ../spalloc/spalloc_client ../spalloc/tests \
     ../SpiNNFrontEndCommon/spinn_front_end_common ../SpiNNFrontEndCommon/unittests \
     ../SpiNNFrontEndCommon/fec_integration_tests \
     spynnaker unittests spynnaker_integration_tests proxy_integration_tests \
     --target-version py310 --config ../SupportScripts/actions/ruff/ruff_up.toml