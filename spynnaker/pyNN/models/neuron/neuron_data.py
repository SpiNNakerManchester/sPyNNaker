# Copyright (c) 2022 The University of Manchester
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
from typing import Iterator, MutableMapping, Optional, Tuple, cast
from typing_extensions import Never

import numpy
from numpy import uint32
from numpy.typing import NDArray

from spinn_utilities.helpful_functions import is_singleton
from spinn_utilities.ranged import RangeDictionary, RangedList

from pacman.model.graphs.common import Slice
from pacman.model.placements import Placement

from spinn_front_end_common.interface.ds import DataSpecificationBase
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)

from spynnaker.pyNN.utilities.struct import Struct, StructRepeat
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron.population_vertex import (
    PopulationVertex)
from spynnaker.pyNN.models.neuron.population_machine_neurons import (
    NeuronRegions)


def _all_one_val_gen(rd: RangeDictionary[float]) -> bool:
    """
    Determine if all the values of a dictionary are the same, assuming we
    already know that they are generatable

    .. note::
        A random distribution is considered the same if the same distribution
        is used for all neurons.
    """
    for key in rd.keys():
        if is_singleton(rd[key]):
            return True
        if not rd[key].range_based():
            return False
        for i, (_start, _stop, _val) in enumerate(rd[key].iter_ranges()):
            if i > 0:
                return False
    return True


class NeuronData(object):
    """
    Holds and creates the data for a group of neurons.
    """

    __slots__ = (
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
        "__gen_on_machine")

    def __init__(self, app_vertex: PopulationVertex):
        self.__app_vertex = app_vertex
        self.__neuron_data: Optional[NDArray[uint32]] = None
        self.__neuron_recording_data: Optional[NDArray[uint32]] = None
        self.__generation_done = False
        self.__gen_on_machine = False
        self.__neuron_data_n_structs = 0

    @property
    def gen_on_machine(self) -> bool:
        """
        Whether the neuron data can be generated on the machine or not.
        """
        return self.__gen_on_machine

    def generate_data(self) -> None:
        """
        Do the data generation internally.
        """
        if self.__generation_done:
            return
        self.__generation_done = True

        if not self.__app_vertex.can_generate_on_machine():
            self.__gen_on_machine = False
            return

        # Check that all parameters and state variables have a single range
        params = self.__app_vertex.parameters
        state_vars = self.__app_vertex.state_variables
        if not _all_one_val_gen(params) or not _all_one_val_gen(state_vars):
            # Note at this point, we can still generate ranges on machine,
            # just that it has to be different per core
            self.__gen_on_machine = True
            self.__neuron_data = None
            return

        # Go through all the structs and make all the data
        structs = self.__app_vertex.neuron_impl.structs
        values = _MergedDict(params, state_vars)
        all_data = [struct.get_generator_data(values) for struct in structs]
        self.__neuron_data = numpy.concatenate(all_data)
        self.__neuron_data_n_structs = len(structs)

        # Get the neuron recording data
        neuron_recorder = self.__app_vertex.neuron_recorder
        if neuron_recorder.is_global_generatable:
            self.__neuron_recording_data = neuron_recorder.get_generator_data()

        # If we get here, we know everything is generated on machine
        self.__gen_on_machine = True

    def write_data(self, spec: DataSpecificationBase, vertex_slice: Slice,
                   neuron_regions: NeuronRegions,
                   gen_on_machine: bool = True) -> None:
        """
        Write the generated data.

        :param spec: The data specification to write to
        :param vertex_slice: The vertex slice to generate for
        :param neuron_regions: The regions to write to
        :param gen_on_machine: Whether to allow generation on machine
        """
        if gen_on_machine:
            self.generate_data()
        spec.reserve_memory_region(
            region=neuron_regions.neuron_params,
            size=self.__app_vertex.get_sdram_usage_for_neuron_params(
                    vertex_slice.n_atoms),
            label="neuron_params")
        neuron_recorder = self.__app_vertex.neuron_recorder
        spec.reserve_memory_region(
            region=neuron_regions.neuron_recording,
            size=neuron_recorder.get_metadata_sdram_usage_in_bytes(
                vertex_slice.n_atoms),
            label="neuron recording")
        if self.gen_on_machine and gen_on_machine:
            if self.__neuron_data is not None:
                data = self.__neuron_data
                n_structs = self.__neuron_data_n_structs
            else:
                n_structs, data = self.__get_neuron_builder_data(vertex_slice)
            header = self.__get_neuron_builder_header(
                vertex_slice, n_structs, neuron_regions)
            if self.__neuron_recording_data is not None:
                rec_data = self.__neuron_recording_data
            else:
                rec_data = neuron_recorder.get_generator_data(vertex_slice)
            n_words = len(data) + len(header) + len(rec_data)
            spec.reserve_memory_region(
                region=neuron_regions.neuron_builder,
                size=n_words * BYTES_PER_WORD,
                label="neuron_builder")
            spec.switch_write_focus(neuron_regions.neuron_builder)
            spec.write_array(header)
            spec.write_array(data)
            spec.write_array(rec_data)
        else:
            spec.switch_write_focus(neuron_regions.neuron_params)
            neuron_data = self.__get_neuron_param_data(vertex_slice)
            spec.write_array(neuron_data)
            neuron_recorder.write_neuron_recording_region(
                spec, neuron_regions.neuron_recording, vertex_slice)
        spec.reserve_memory_region(
            region=neuron_regions.initial_values,
            size=self.__app_vertex.get_sdram_usage_for_neuron_params(
                    vertex_slice.n_atoms),
            label="initial_values")

    def __get_neuron_param_data(self, vertex_slice: Slice) -> NDArray:
        """
        Get neuron parameter data for a slice.

        :param vertex_slice: The slice to get the data for
        """
        structs = self.__app_vertex.neuron_impl.structs
        values = _MergedDict(self.__app_vertex.parameters,
                             self.__app_vertex.state_variables)
        return numpy.concatenate([
            self.__get_struct_data(struct, values, vertex_slice)
            for struct in structs])

    def __get_struct_data(self, struct: Struct, values: '_MergedDict',
                          vertex_slice: Slice) -> NDArray[uint32]:
        """
        Get the data for a structure.

        :param struct: The structure to get the data for
        :param values: The values to fill in the structure with
        :param vertex_slice: The slice to get the values for
        """
        if struct.repeat_type == StructRepeat.GLOBAL:
            return struct.get_data(values)
        return struct.get_data(values, vertex_slice)

    def __get_neuron_builder_data(
            self, vertex_slice: Slice) -> Tuple[int, NDArray[uint32]]:
        """
        Get the data to build neuron parameters with.

        :param vertex_slice: The slice to get the parameters for
        :return: The number of structures and the data
        """
        structs = self.__app_vertex.neuron_impl.structs
        values = _MergedDict(self.__app_vertex.parameters,
                             self.__app_vertex.state_variables)
        return len(structs), numpy.concatenate([
            self.__get_builder_data(struct, values, vertex_slice)
            for struct in structs])

    def __get_builder_data(
            self, struct: Struct, values: '_MergedDict',
            vertex_slice: Slice) -> NDArray[uint32]:
        """
        Get the builder data for a structure.

        :param struct: The structure to get the data for
        :param values: The values to fill in the structure with
        :param vertex_slice: The slice to get the values for
        """
        if struct.repeat_type == StructRepeat.GLOBAL:
            return struct.get_generator_data(values)
        return struct.get_generator_data(values, vertex_slice)

    def __get_neuron_builder_header(
            self, vertex_slice: Slice, n_structs: int,
            neuron_regions: NeuronRegions) -> NDArray[uint32]:
        """
        Get the header of the neuron builder region.

        :param vertex_slice: The slice to put in the header
        :param n_structs: The number of structures to generate
        :param neuron_regions: The regions to point to
        """
        return numpy.array([
            neuron_regions.neuron_params,
            neuron_regions.neuron_recording,
            *self.__app_vertex.pop_seed,
            *self.__app_vertex.core_seed(vertex_slice),
            n_structs, vertex_slice.n_atoms], dtype=uint32)

    def read_data(self, placement: Placement,
                  neuron_regions: NeuronRegions) -> None:
        """
        Read the current state of the data from the machine into the
        application vertex.

        :param placement:
            The placement of the vertex to read
        :param neuron_regions: The regions to read from
        """
        merged_dict = _MergedDict(self.__app_vertex.parameters,
                                  self.__app_vertex.state_variables)
        self.__do_read_data(
            placement, neuron_regions.neuron_params, merged_dict)

    def read_initial_data(self, placement: Placement,
                          neuron_regions: NeuronRegions) -> None:
        """
        Read the initial state of the data from the machine into the
        application vertex.

        :param placement:
            The placement of the vertex to read
        :param neuron_regions: The regions to read from
        """
        merged_dict = _MergedDict(self.__app_vertex.parameters,
                                  self.__app_vertex.initial_state_variables)
        self.__do_read_data(
            placement, neuron_regions.initial_values, merged_dict)

    def __do_read_data(self, placement: Placement, region: int,
                       results: '_MergedDict') -> None:
        """
        Perform the reading of data.

        :param placement: Where the vertex is on the machine
        :param region: The region to read from
        :param results: Where to write the results to
        """
        address = locate_memory_region_for_placement(placement, region)
        vertex_slice = placement.vertex.vertex_slice
        data_size = self.__app_vertex.get_sdram_usage_for_neuron_params(
            vertex_slice.n_atoms)
        block = SpynnakerDataView.read_memory(
            placement.x, placement.y, address, data_size)
        offset = 0
        for struct in self.__app_vertex.neuron_impl.structs:
            if struct.repeat_type == StructRepeat.GLOBAL:
                struct.read_data(block, cast(RangeDictionary, results), offset)
                offset += struct.get_size_in_whole_words() * BYTES_PER_WORD
            else:
                struct.read_data(block, cast(RangeDictionary, results), offset,
                                 vertex_slice)
                offset += (
                    struct.get_size_in_whole_words(vertex_slice.n_atoms) *
                    BYTES_PER_WORD)

    def reset_generation(self) -> None:
        """
        Reset generation so it is done again.
        """
        self.__neuron_data = None
        self.__neuron_recording_data = None
        self.__generation_done = False
        self.__gen_on_machine = False
        self.__neuron_data_n_structs = 0


class _MergedDict(MutableMapping[str, RangedList[float]]):
    __slots__ = (
        "__params",
        "__state_vars")

    def __init__(self, params: RangeDictionary[float],
                 state_vars: RangeDictionary[float]):
        self.__params = params
        self.__state_vars = state_vars

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return key in self.__params or key in self.__state_vars

    def __getitem__(self, key: str) -> RangedList[float]:
        if key in self.__params:
            return self.__params[key]
        return self.__state_vars[key]

    def __setitem__(self, key: str, value: RangedList[float]) -> None:
        if key in self.__params:
            self.__params[key] = value
        elif key in self.__state_vars:
            self.__state_vars[key] = value
        else:
            raise KeyError(f"No such key {key}")

    def __delitem__(self, __v: str) -> Never:
        raise NotImplementedError("items may not be deleted")

    def __iter__(self) -> Iterator[str]:
        yield from self.__params.keys()
        yield from self.__state_vars.keys()

    def __len__(self) -> int:
        return len(self.__params) + len(self.__state_vars)
