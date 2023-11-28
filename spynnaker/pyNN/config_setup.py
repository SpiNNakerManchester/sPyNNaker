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
from spinn_utilities.config_holder import (
    clear_cfg_files, set_cfg_files)
from spinn_front_end_common.interface.config_setup import (
    add_default_cfg, add_spinnaker_cfg)
from spynnaker.pyNN.data.spynnaker_data_writer import SpynnakerDataWriter

CONFIG_FILE_NAME = "spynnaker.cfg"


def setup_configs() -> None:
    """
    Sets up the configurations including the users configuration file.

    Clears out any previous read configurations but does not load the new
    configurations so a warning is generated if a configuration is used before
    setup is called.
    """
    clear_cfg_files(False)
    add_spinnaker_cfg()  # This add its dependencies too
    set_cfg_files(
        config_file=CONFIG_FILE_NAME,
        default=os.path.join(os.path.dirname(__file__), CONFIG_FILE_NAME))


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


def add_spynnaker_cfg() -> None:
    add_spinnaker_cfg()  # This add its dependencies too
    add_default_cfg(os.path.join(os.path.dirname(__file__), CONFIG_FILE_NAME))
