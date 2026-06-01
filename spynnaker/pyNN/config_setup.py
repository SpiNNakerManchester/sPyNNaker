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

import os
from typing import Set

from spinn_utilities.config_holder import clear_cfg_files
from spinn_front_end_common.interface.config_setup import (
    add_default_cfg, add_spinnaker_cfg)
from spinn_front_end_common.interface.config_setup import (
    fec_cfg_paths_skipped)

from spynnaker.pyNN.data.spynnaker_data_writer import SpynnakerDataWriter
from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModel

SPYNNAKER_CFG = "spynnaker.cfg"


def unittest_setup() -> None:
    """
    Does all the steps that may be required before a unit-test.

    Resets the configurations so only the local default configurations are
    included.
    The user configuration is *not* included!

    Unsets any previous simulators and temporary directories

    .. note::
         This file should only be called from sPyNNaker tests
         that do not call `sim.setup`
    """
    clear_cfg_files(True)
    add_spynnaker_cfg()
    SpynnakerDataWriter.mock()
    AbstractPyNNNeuronModel.reset_all()


def add_spynnaker_cfg() -> None:
    """
    Add the local configuration and all dependent configuration files.
    """
    add_spinnaker_cfg()  # This add its dependencies too
    add_default_cfg(os.path.join(os.path.dirname(__file__), SPYNNAKER_CFG))


def cfg_paths_skipped() -> Set[str]:
    """
    Set of cfg path that would not be found based on other cfg settings

    Assuming mode = Debug

    :returns:
       List of cfg Option names that point to paths unlikely to be used.
    """
    return fec_cfg_paths_skipped()
