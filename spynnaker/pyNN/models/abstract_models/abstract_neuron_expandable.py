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

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.require_subclass import require_subclass
from pacman.model.graphs.machine import MachineVertex
from pacman.model.placements import Placement

NEURON_EXPANDER_APLX = "neuron_expander.aplx"


@require_subclass(MachineVertex)
class AbstractNeuronExpandable(object, metaclass=AbstractBase):
    """
    Indicates a class (a
    :py:class:`~pacman.model.graphs.machine.MachineVertex`)
    that has may need to run the neuron expander APLX.
    """

    __slots__ = ()

    @abstractmethod
    def gen_neurons_on_machine(self) -> bool:
        """
        True if the neurons of a the slice of this vertex should be
        generated on the machine.

        .. note::
            The typical implementation for this method will be to ask the
            neuron data

        :rtype: bool
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def neuron_generator_region(self) -> int:
        """
        The region containing the parameters of neuron expansion.

        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def read_generated_initial_values(self, placement: Placement):
        """
        Fill in any requested initial values.

        :param ~pacman.model.placements.Placement placement:
            Where the data is on the machine
        """
        raise NotImplementedError
