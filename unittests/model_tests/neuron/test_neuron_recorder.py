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

import numpy
from data_specification.enums import DataType
from unittests.mocks import MockSimulator
from pacman.model.graphs.common import Slice
from spinn_front_end_common.utilities import globals_variables
from spynnaker.pyNN.models.common import NeuronRecorder
from spynnaker.pyNN.utilities.spynnaker_failed_state import (
    SpynnakerFailedState)


def test_simple_record():
    simulator = MockSimulator()
    globals_variables.set_failed_state(SpynnakerFailedState())
    globals_variables.set_simulator(simulator)

    recordables = ["v", "gsyn_exc", "gsyn_inh"]

    data_types = {
        "v": DataType.S1615,
        "gsyn_exc": DataType.S1615,
        "gsyn_inh": DataType.S1615
    }
    nr = NeuronRecorder(recordables, data_types, [], 0, 100, 1000)

    assert(frozenset(["v", "gsyn_exc", "gsyn_inh"]) ==
           frozenset(nr.get_recordable_variables()))
    assert([] == nr.recording_variables)
    nr.set_recording("v", True)
    assert(["v"] == nr.recording_variables)
    _slice = Slice(0, 50)
    gps = nr.get_global_parameters(_slice)
    # 3 rates (index "0" is v)
    assert (gps[0].get_value() == 1)
    # 3 n_neurons  (index "3" is v)
    assert (gps[3].get_value() == _slice.n_atoms)


def test_recording_variables():
    simulator = MockSimulator()
    globals_variables.set_failed_state(SpynnakerFailedState())
    globals_variables.set_simulator(simulator)

    recordables = ["v", "gsyn_exc", "gsyn_inh"]

    data_types = {
        "v": DataType.S1615,
        "gsyn_exc": DataType.S1615,
        "gsyn_inh": DataType.S1615
    }

    nr = NeuronRecorder(recordables, data_types, [], 0, 100, 1000)
    assert([] == nr.recording_variables)
    nr.set_recording("v", True)
    nr.set_recording("gsyn_inh", True)
    assert(["v", "gsyn_inh"] == nr.recording_variables)
    assert([0, 2] == nr.recorded_region_ids)


def test_pack_matrix():
    original = numpy.array([1, 2, 3, 31, 32, 33, 61, 62, 63, 91, 92, 93]).\
        reshape(4, 3)
    ratio = 3
    result = NeuronRecorder.pack_matrix(original, ratio)
    target = numpy.array(
        [1, 2, 3,
         numpy.nan, numpy.nan, numpy.nan,
         numpy.nan, numpy.nan, numpy.nan,
         31, 32, 33,
         numpy.nan, numpy.nan, numpy.nan,
         numpy.nan, numpy.nan, numpy.nan,
         61, 62, 63,
         numpy.nan, numpy.nan, numpy.nan,
         numpy.nan, numpy.nan, numpy.nan,
         91, 92, 93,
         numpy.nan, numpy.nan, numpy.nan,
         numpy.nan, numpy.nan, numpy.nan]).reshape(12, 3)
    assert(result.shape == target.shape)
    numpy.testing.assert_equal(result, target)


def test_combine_matrix():
    org1 = numpy.array([1, 2, 3,
                        11, 12, 13,
                        21, 22, 23,
                        31, 32, 33,
                        41, 42, 43,
                        51, 52, 53,
                        61, 62, 63,
                        71, 72, 73,
                        81, 82, 83,
                        91, 92, 93,
                        101, 102, 103,
                        111, 112, 113]). \
            reshape(12, 3)
    org2 = numpy.array([21, 22, 23,
                        221, 222, 223,
                        241, 242, 243,
                        261, 262, 263,
                        281, 282, 283,
                        2101, 2102, 2103]).\
        reshape(6, 3)
    org3 = numpy.array([31, 32, 33,
                        331, 332, 333,
                        361, 362, 363,
                        391, 392, 393]).\
        reshape(4, 3)
    result2_3, indexex2_3, interval2_3 = \
        NeuronRecorder.combine_matrix([org2, org3],
                                      [[4, 5, 6], [7, 8, 9]],
                                      [2000, 3000])
    assert(result2_3.shape == (12, 6))
    assert(interval2_3 == 1000)
    nan = numpy.nan
    target2_3 = numpy.array([21, 22, 23, 31, 32, 33,
                             nan, nan, nan, nan, nan, nan,
                             221, 222, 223, nan, nan, nan,
                             nan, nan, nan, 331, 332, 333,
                             241, 242, 243, nan, nan, nan,
                             nan, nan, nan, nan, nan, nan,
                             261, 262, 263, 361, 362, 363,
                             nan, nan, nan, nan, nan, nan,
                             281, 282, 283, nan, nan, nan,
                             nan, nan, nan, 391, 392, 393,
                             2101, 2102, 2103, nan, nan, nan,
                             nan, nan, nan, nan, nan, nan]).reshape(12, 6)
    numpy.testing.assert_equal(result2_3, target2_3)
    result1_2_3, indexex1_2_3, interval1_2_3 = \
        NeuronRecorder.combine_matrix([org1, org2, org3],
                                      [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                                      [1000, 2000, 3000])
    assert(result1_2_3.shape == (12, 9))
    assert(interval1_2_3 == 1000)
    numpy.array_equal(indexex1_2_3, [1, 2, 3, 4, 5, 6, 7, 8, 9])
    target1_2_3 = numpy.array(
        [1, 2, 3, 21, 22, 23, 31, 32, 33,
         11, 12, 13, nan, nan, nan, nan, nan, nan,
         21, 22, 23, 221, 222, 223, nan, nan, nan,
         31, 32, 33, nan, nan, nan, 331, 332, 333,
         41, 42, 43, 241, 242, 243, nan, nan, nan,
         51, 52, 53, nan, nan, nan, nan, nan, nan,
         61, 62, 63, 261, 262, 263, 361, 362, 363,
         71, 72, 73, nan, nan, nan, nan, nan, nan,
         81, 82, 83, 281, 282, 283, nan, nan, nan,
         91, 92, 93, nan, nan, nan, 391, 392, 393,
         101, 102, 103, 2101, 2102, 2103, nan, nan, nan,
         111, 112, 113, nan, nan, nan, nan, nan, nan]).reshape(12, 9)
    numpy.testing.assert_equal(result1_2_3, target1_2_3)
