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
import spynnaker.pyNN.utilities.utility_calls as utility_calls


def check_gsyn(gsyn1, gsyn2):
    """ Compare two arrays of conductances. For testing.

    :param gsyn1: An array of conductances.
    :param gsyn2: An array of conductances.
    :raises ValueError: If the arrays differ.
    """
    if len(gsyn1) != len(gsyn2):
        raise ValueError(f"Length of gsyn does not match expected "
                         f"{len(gsyn1)} but found {len(gsyn2)}")
    for gsyn1i, i in enumerate(gsyn1):
        for j in range(3):
            if round(gsyn1i[j], 1) != round(gsyn2[i][j], 1):
                raise ValueError(
                    f"Mismatch between gsyn found at position {i}{j} "
                    f"expected {gsyn1i[j]} but found {gsyn2[i][j]}")


def check_path_gysn(path, n_neurons, runtime, gsyn):
    """ Compare an arrays of conductances with baseline data from a file. \
        For testing.

    :param path: A file path.
    :param n_neurons: The number of neurons that produced the data.
    :param runtime: The length of time that the generated data represents.
    :param gsyn: An array of conductances.
    :raises ValueError: If the arrays differ.
    """
    gsyn2 = utility_calls.read_in_data_from_file(
        path, 0, n_neurons, 0, runtime, True)
    check_gsyn(gsyn, gsyn2)


def check_sister_gysn(sister, n_neurons, runtime, gsyn):
    """ Compare an arrays of conductances with baseline data from a file next\
        to a specified module. For testing.

    :param sister: A module. The file read from will be ``gsyn.data``
        adjacent to this module.
    :param n_neurons: The number of neurons that produced the data.
    :param runtime: The length of time that the generated data represents.
    :param gsyn: An array of conductances.
    :raises ValueError: If the arrays differ.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(sister)), "gsyn.data")
    check_path_gysn(path, n_neurons, runtime, gsyn)
