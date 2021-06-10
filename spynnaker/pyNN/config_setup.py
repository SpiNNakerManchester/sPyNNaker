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

import os
from spinn_utilities.config_holder import (
    clear_cfg_files, set_cfg_files)
from spinn_front_end_common.interface.config_setup import (
    add_default_cfg, add_spinnaker_cfg)
from spinn_front_end_common.utilities.globals_variables import unset_simulator

CONFIG_FILE_NAME = "spynnaker.cfg"


def setup_configs():
    """
    Sets up the configs including the users cfg file

    Clears out any previous read configs but does not load the new configs
    so a warning is generated if a config is used before setup is called.

    """
    clear_cfg_files(False)
    add_spinnaker_cfg()  # This add its dependencies too
    set_cfg_files(
        configfile=CONFIG_FILE_NAME,
        default=os.path.join(os.path.dirname(__file__), CONFIG_FILE_NAME))


def unittest_setup():
    """
    Does all the steps that may be required before a unittest

    Resets the configs so only the local default configs are included.
    The user cfg is NOT included!

    Unsets any previous simulators and tempdirs

    .. note::
         This file should only be called from Spynnaker tests
         that do not call sim.setup

    """
    unset_simulator()
    clear_cfg_files(True)
    add_spinnaker_cfg()  # This add its dependencies too
    add_default_cfg(os.path.join(os.path.dirname(__file__), CONFIG_FILE_NAME))
