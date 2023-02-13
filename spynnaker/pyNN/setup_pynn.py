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
    with open(spinnaker_init, "w", encoding="utf-8") as spinn_file:
        spinn_file.write("from spynnaker.pyNN import *\n")
        # To revert back to spynnaker8 use this line instead of the above
        # spinn_file.write("from spynnaker8 import *\n")

    print(f"Created {spinnaker_init} to point to spynnaker.pyNN")


def setup_pynn():
    # Perform the installation
    install_sPyNNaker_into(pyNN)


# Check the version; we really want PyNN 0.9
if not version_satisfies(pyNN, "0.9"):
    raise NotImplementedError(
        f"PyNN version {pyNN.__version__} found; "
        f"sPyNNaker requires PyNN version 0.9")

setup_pynn()
