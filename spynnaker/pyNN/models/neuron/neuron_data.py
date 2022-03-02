# Copyright (c) 2022 The University of Manchester
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
from spynnaker.pyNN.models.common.param_generator_data import (
    is_param_generatable)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spynnaker.pyNN.utilities.struct import StructRepeat
from spinn_utilities.helpful_functions import is_singleton


def _all_one_val_gen(rd):
    """ Determine if all the values of a dictionary are the same,
        and can be generated.  Note that a random distribution is considered
        the same if the same distribution is used for all neurons.

    :rtype: bool
    """
    for key in rd.keys():
        if is_singleton(rd[key]):
            if not is_param_generatable(rd[key]):
                return False
        else:
            if not rd[key].range_based():
                return False
            for i, (_start, _stop, val) in enumerate(rd[key].iter_ranges()):
                if i > 1:
                    return False
                if not is_param_generatable(val):
                    return False
    return True


def _all_gen(rd):
    """ Determine if all the values of a ranged dictionary can be generated.

    :rtype: bool
    """
    for key in rd.keys():
        if is_singleton(rd[key]):
            if not is_param_generatable(rd[key]):
                return False
        else:
            if not rd[key].range_based():
                return False
            for _start, _stop, val in rd[key].iter_ranges():
                if not is_param_generatable(val):
                    return False
    return True


class NeuronData(object):
    """ Holds and creates the data for a group of neurons
    """

    __slots__ = [
        # The neuron regions to be used
        "__neuron_regions",

        # The application vertex
        "__app_vertex",

        # The data to be written for all vertices, if applicable
        "__neuron_data",

        # The number of structs in neuron_data
        "__neuron_data_n_structs",

        # The neuron recording data for all vertices, if applicable
        "__neuron_recording_data",

        # Whether an attempt has been made to generate neuron data
        "__generation_done",

        # Whether to generate things on the machine
        "__gen_on_machine"
    ]

    def __init__(self, neuron_regions, app_vertex):
        self.__neuron_regions = neuron_regions
        self.__app_vertex = app_vertex
        self.__neuron_data = None
        self.__neuron_recording_data = None
        self.__generation_done = False
        self.__gen_on_machine = None

    @property
    def gen_on_machine(self):
        return False
        if self.__gen_on_machine is None:
            # First try to generate data.  This might have already been done.
            self.generate_data()
            if self.__gen_on_machine is not None:
                return self.__gen_on_machine

            # If we get here, we know the structs are fine so check params
            params = self.__app_vertex.parameters
            state_vars = self.__app_vertex.state_variables
            self.__gen_on_machine = _all_gen(params) and _all_gen(state_vars)
        return self.__gen_on_machine

    def generate_data(self):
        return
        if self.__generation_done:
            return
        self.__generation_done = True

        # Check that all the structs can actually be generated
        structs = self.__app_vertex.neuron_impl.structs
        for struct in structs:
            if not struct.is_generatable:
                # If this is false, we can't generate anything on machine
                self.__gen_on_machine = False
                return

        params = self.__app_vertex.parameters
        state_vars = self.__app_vertex.state_variables
        pre_computed = self.__app_vertex.neuron_impl.get_precomputed_values(
            params, state_vars)

        # Check that all parameters and state variables have a single range
        if (not _all_one_val_gen(params) or not _all_one_val_gen(state_vars) or
                not _all_one_val_gen(pre_computed)):
            # Note at this point, we might still be able to generate ranges
            # on machine
            return

        # Go through all the structs and make all the data
        values = _MergedDict(params, state_vars, pre_computed)
        all_data = [struct.get_generator_data(values) for struct in structs]
        self.__neuron_data = numpy.concatenate(all_data)
        self.__neuron_data_n_structs = len(structs)

        # Get the neuron recording data
        neuron_recorder = self.__app_vertex.neuron_recorder
        if neuron_recorder.is_global_generatable:
            self.__neuron_recording_data = neuron_recorder.get_generator_data()

        # If we get here, we know everything is generated on machine
        self.__gen_on_machine = True

    def write_data(self, spec, vertex_slice):
        self.generate_data()
        spec.reserve_memory_region(
            region=self.__neuron_regions.neuron_params,
            size=self.__app_vertex.get_sdram_usage_for_neuron_params(
                    vertex_slice.n_atoms),
            label="neuron_params")
        neuron_recorder = self.__app_vertex.neuron_recorder
        spec.reserve_memory_region(
            region=self.__neuron_regions.neuron_recording,
            size=neuron_recorder.get_metadata_sdram_usage_in_bytes(
                vertex_slice.n_atoms),
            label="neuron recording")
        if self.gen_on_machine:
            if self.__neuron_data is not None:
                data = self.__neuron_data
                n_structs = self.__neuron_data_n_structs
            else:
                n_structs, data = self.__get_neuron_builder_data(vertex_slice)
            header = self.__get_neuron_builder_header(vertex_slice, n_structs)
            if self.__neuron_recording_data is not None:
                rec_data = self.__neuron_recording_data
            else:
                rec_data = neuron_recorder.get_generator_data(vertex_slice)
            n_words = len(data) + len(header) + len(rec_data)
            spec.reserve_memory_region(
                region=self.__neuron_regions.neuron_builder,
                size=n_words * BYTES_PER_WORD,
                label="neuron_builder")
            spec.switch_write_focus(self.__neuron_regions.neuron_builder)
            spec.write_array(header)
            spec.write_array(data)
            spec.write_array(rec_data)
        else:
            spec.switch_write_focus(self.__neuron_regions.neuron_params)
            neuron_data = self.__get_neuron_param_data(vertex_slice)
            spec.write_array(neuron_data)
            neuron_recorder.write_neuron_recording_region(
                spec, self.__neuron_regions.neuron_recording,
                vertex_slice)

    def __get_neuron_param_data(self, vertex_slice):
        structs = self.__app_vertex.neuron_impl.structs
        params = self.__app_vertex.parameters
        state_vars = self.__app_vertex.state_variables
        pre_computed = self.__app_vertex.neuron_impl.get_precomputed_values(
            params, state_vars)
        values = _MergedDict(params, state_vars, pre_computed)
        all_data = [
            self.__get_struct_data(struct, values, vertex_slice)
            for struct in structs]
        return numpy.concatenate(all_data)

    def __get_struct_data(self, struct, values, vertex_slice):
        if struct.repeat_type == StructRepeat.GLOBAL:
            return struct.get_data(values)
        return struct.get_data(
            values, vertex_slice.lo_atom, vertex_slice.n_atoms)

    def __get_neuron_builder_data(self, vertex_slice):
        structs = self.__app_vertex.neuron_impl.structs
        params = self.__app_vertex.parameters
        state_vars = self.__app_vertex.state_variables
        values = _MergedDict(params, state_vars)
        all_data = [
            self.__get_builder_data(struct, values, vertex_slice)
            for struct in structs]
        return len(structs), numpy.concatenate(all_data)

    def __get_builder_data(self, struct, values, vertex_slice):
        if struct.repeat_type == StructRepeat.GLOBAL:
            return struct.get_generator_data(values)
        return struct.get_generator_data(
            values, vertex_slice.lo_atom, vertex_slice.n_atoms)

    def __get_neuron_builder_header(self, vertex_slice, n_structs):
        return numpy.array([
            self.__neuron_regions.neuron_params,
            self.__neuron_regions.neuron_recording,
            *self.__app_vertex.pop_seed, *self.__app_vertex.core_seed,
            n_structs, vertex_slice.n_atoms
        ], dtype="uint32")

    def read_data(self, transceiver, placement, vertex_slice):
        address = locate_memory_region_for_placement(
            placement, self.__neuron_regions.neuron_params, transceiver)
        data_size = self.__app_vertex.get_sdram_usage_for_neuron_params(
            vertex_slice.n_atoms)
        block = transceiver.read_memory(
            placement.x, placement.y, address, data_size)
        # Only update data from state variables
        state_vars = self.__app_vertex.state_variables
        offset = 0
        for struct in self.__app_vertex.neuron_impl.structs:
            struct.read_data(block, state_vars, offset, vertex_slice.lo_atom,
                             vertex_slice.n_atoms)


class _MergedDict(object):
    __slots__ = [
        "__params",
        "__state_vars",
        "__pre_calculated"
    ]

    def __init__(self, params, state_vars, pre_calculated):
        self.__params = params
        self.__state_vars = state_vars
        self.__pre_calculated = pre_calculated

    def __contains__(self, key):
        return (key in self.__params or key in self.__state_vars or
                key in self.__pre_calculated)

    def __getitem__(self, key):
        if key in self.__params:
            return self.__params[key]
        if key in self.__state_vars:
            return self.__state_vars[key]
        return self.__pre_calculated[key]
