# Copyright (c) 2017-2022 The University of Manchester
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

"""
This script installs sPyNNaker so that it usable as the ``pyNN.spiNNaker``
module.

.. note::
    This *modifies* your pyNN installation!
"""

import os
from distutils.version import StrictVersion as Version  # pylint: disable=all
import pyNN


def version_satisfies(module, requirement):
    """ Perform a version check. This code could be smarter...
    """
    return Version(module.__version__) >= Version(requirement)


def install_sPyNNaker_into(module):
    """ Do the actual installation by creating a package within the given\
        module's implementation. This is very nasty!
    """
    spinnaker_dir = os.path.join(os.path.dirname(module.__file__), "spiNNaker")
    if not os.path.exists(spinnaker_dir):
        os.mkdir(spinnaker_dir)

    spinnaker_init = os.path.join(spinnaker_dir, "__init__.py")
    with open(spinnaker_init, "w") as spinn_file:
        spinn_file.write("from spynnaker.pyNN import *\n")

    print(f"Created {spinnaker_init} to point to spynnaker.pyNN")


def setup_pynn():
    # Perform the installation
    install_sPyNNaker_into(pyNN)


# Check the version; we really want PyNN 0.9
if not version_satisfies(pyNN, "0.9"):
    raise Exception(
        f"PyNN version {pyNN.__version__} found; "
        f"sPyNNaker requires PyNN version 0.9")

setup_pynn()
