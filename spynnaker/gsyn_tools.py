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
import spynnaker.pyNN.utilities.utility_calls as utility_calls


def check_gsyn(gsyn1, gsyn2):
    if len(gsyn1) != len(gsyn2):
        raise Exception("Length of gsyn does not match expected {} but "
                        "found {}".format(len(gsyn1), len(gsyn2)))
    for i in range(len(gsyn1)):  # pylint: disable=consider-using-enumerate
        for j in range(3):
            if round(gsyn1[i][j], 1) != round(gsyn2[i][j], 1):
                raise Exception("Mismatch between gsyn found at position {}{}"
                                "expected {} but found {}".
                                format(i, j, gsyn1[i][j], gsyn2[i][j]))


def check_path_gysn(path, n_neurons, runtime, gsyn):
    gsyn2 = utility_calls.read_in_data_from_file(
        path, 0, n_neurons, 0, runtime, True)
    check_gsyn(gsyn, gsyn2)


def check_sister_gysn(sister, n_neurons, runtime, gsyn):
    path = os.path.join(os.path.dirname(os.path.abspath(sister)), "gsyn.data")
    check_path_gysn(path, n_neurons, runtime, gsyn)
