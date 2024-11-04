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

# This bash assumes that other repositories are installed in paralled

# requires the latest mypy
# pip install --upgrade mypy

utils="../SpiNNUtils/spinn_utilities"
machine="../SpiNNMachine/spinn_machine"
man="../SpiNNMan/spinnman"
pacman="../PACMAN/pacman"
spalloc="../spalloc/spalloc_client"
fec="../SpiNNFrontEndCommon/spinn_front_end_common"

mypy --python-version 3.8 $utils $machine $man $pacman $spalloc $fec spynnaker
