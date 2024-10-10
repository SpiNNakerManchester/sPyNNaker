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

from typing import Optional
from spinn_utilities.overrides import overrides
from pacman.model.partitioner_splitters import AbstractSplitterCommon
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from .spike_injector_vertex import SpikeInjectorVertex

_population_parameters = {
    "port": None,
    "virtual_key": None,
    "reserve_reverse_ip_tag": False,
    "splitter": None
}


class SpikeInjector(AbstractPyNNModel):
    """
    Model that creates a Spike Injector Vertex
    """
    __slots__ = ()

    default_population_parameters = _population_parameters

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=_population_parameters.keys())
    def create_vertex(
            self, n_neurons: int, label: str, *,
            port: Optional[int] = None, virtual_key: Optional[int] = None,
            reserve_reverse_ip_tag: bool = False,
            splitter: Optional[AbstractSplitterCommon] = None) \
            -> SpikeInjectorVertex:
        """
        :param int port:
        :param int virtual_key:
        :param bool reserve_reverse_ip_tag:
        :param splitter:
        :type splitter:
            ~pacman.model.partitioner_splitters.AbstractSplitterCommon or None
        """
        # pylint: disable=arguments-differ
        max_atoms_per_core = self.get_model_max_atoms_per_dimension_per_core()
        return SpikeInjectorVertex(
            n_neurons, label, port, virtual_key,
            reserve_reverse_ip_tag, splitter, max_atoms_per_core)
