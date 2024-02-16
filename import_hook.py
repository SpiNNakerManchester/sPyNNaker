# Copyright (c) 2017 The University of Manchester
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

"""
This file is imported by init-hook in the rcfile
https://github.com/SpiNNakerManchester/SupportScripts/blob/master/actions/pylint/strict_rcfile

It allows you to temporarily add the other spinnaker repositories without making them part of the permemnant python path

Intended for use when running pylint.bash
"""
import sys
sys.path.append("../SpiNNUtils")
sys.path.append("../SpiNNMachine")
sys.path.append("../SpiNNMan")
sys.path.append("../PACMAN")
sys.path.append("../spalloc")
sys.path.append("../SpiNNFrontEndCommon")
