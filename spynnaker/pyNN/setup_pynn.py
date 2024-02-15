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
This script installs sPyNNaker so that it usable as the ``pyNN.spiNNaker``
module.

.. note::
    This *modifies* your pyNN installation!
"""

import os
# TODO: switch to packaging.version
from packaging.version import Version
import pyNN

# The version of PyNN that we really want
_TARGET_PYNN_VERSION = "0.9"


def version_satisfies(module, requirement):
    """
    Perform a version check. This code could be smarter...

    :param ~types.ModuleType module:
    :param str requirement:
    :return: Whether the module's version satisfies the given requirement
    :rtype: bool
    """
    return Version(module.__version__) >= Version(requirement)


def install_sPyNNaker_into(module):
    """
    Do the actual installation by creating a package within the given
    module's implementation. This is very nasty!

    :param ~types.ModuleType module:
    """
    spinnaker_dir = os.path.join(os.path.dirname(module.__file__), "spiNNaker")
    if not os.path.exists(spinnaker_dir):
        os.mkdir(spinnaker_dir)

    spinnaker_init = os.path.join(spinnaker_dir, "__init__.py")
    with open(spinnaker_init, "w", encoding="utf-8") as spinn_file:
        spinn_file.write("from spynnaker.pyNN import *\n")

    print(f"Created {spinnaker_init} to point to spynnaker.pyNN")


def setup_pynn():
    """
    Checks pyNN version and creates the spynnaker model in pynn.
    """
    # Check the version and blow up if it isn't there
    if not version_satisfies(pyNN, _TARGET_PYNN_VERSION):
        raise NotImplementedError(
            f"PyNN version {pyNN.__version__} found; "
            f"sPyNNaker requires PyNN version {_TARGET_PYNN_VERSION}")

    # Perform the installation unless we're on READTHEDOCS
    if os.environ.get('READTHEDOCS', 'False') != 'True':
        install_sPyNNaker_into(pyNN)


if __name__ == "__main__":
    setup_pynn()
