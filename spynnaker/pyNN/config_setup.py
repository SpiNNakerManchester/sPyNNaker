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
from spinn_front_end_common.interface.config_setup import add_spinnaker_cfg

CONFIG_FILE_NAME = "spynnaker.cfg"


def reset_configs():
    """
    Resets the configs so only the local default config is included.

    """
    clear_cfg_files()
    add_spynnaker_cfg()


def add_spynnaker_cfg():
    """
    Add the local cfg and all dependent cfg files.
    """
    add_spinnaker_cfg()  # This add its dependencies too
    set_cfg_files(
        configfile=CONFIG_FILE_NAME,
        default=os.path.join(os.path.dirname(__file__), CONFIG_FILE_NAME))
