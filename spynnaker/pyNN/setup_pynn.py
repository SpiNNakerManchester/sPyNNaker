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
import shutil
from types import ModuleType
from packaging.version import Version
import pyNN
import spynnaker.pyNN as sim


# The version of PyNN that we really want
_TARGET_PYNN_VERSION = "0.9"


def version_satisfies(module: ModuleType, requirement: str) -> bool:
    """
    Perform a version check. This code could be smarter...

    :param module:
    :param requirement:
    :return: Whether the module's version satisfies the given requirement
    """
    return Version(module.__version__) >= Version(requirement)


def install_spynnaker_into(module: ModuleType) -> None:
    """
    Do the actual installation by creating a package within the given
    module's implementation. This is very nasty!

    :param module:
    """
    _file = module.__file__
    assert _file is not None
    spinnaker_dir = os.path.join(os.path.dirname(_file), "spiNNaker")
    if not os.path.exists(spinnaker_dir):
        os.mkdir(spinnaker_dir)

    pynn_init = os.path.join(spinnaker_dir, "__init__.py")
    spynnaker_init = os.path.abspath(sim.__file__)
    shutil.copyfile(spynnaker_init, pynn_init)
    print(f"Updated {pynn_init} to be the same as spynnaker.pyNN")


def setup_pynn() -> None:
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
        install_spynnaker_into(pyNN)


if __name__ == "__main__":
    setup_pynn()
