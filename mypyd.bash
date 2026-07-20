#!/bin/bash

# Copyright (c) 2024 The University of Manchester
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

if [ "$#" -eq  "0" ]
  then
    echo "Provide any argument to run setup"
    source ../SupportScripts/venv/mypy_runner/bin/activate
else
    python3 -m venv ../SupportScripts/venv/mypy_runner
    source ../SupportScripts/venv/mypy_runner/bin/activate
    pip3 install --upgrade ../SpiNNUtils
    pip3 install --upgrade ../SpiNNMachine
    pip3 install --upgrade ../SpiNNMan
    pip3 install --upgrade ../spalloc
    pip3 install --upgrade ../PACMAN
    pip3 install --upgrade ../SpiNNFrontEndCommon
    pip3 install --upgrade ../TestBase
    pip3 install --upgrade ../sPyNNaker[test]
    python3 -m pip install --upgrade mypy
fi

mypy --disallow-untyped-defs spynnaker unittests spynnaker_integration_tests proxy_integration_tests

