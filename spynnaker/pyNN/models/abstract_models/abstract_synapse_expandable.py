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

from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)
from spinn_utilities.require_subclass import require_subclass
from pacman.model.graphs.machine.machine_vertex import MachineVertex

SYNAPSE_EXPANDER_APLX = "synapse_expander.aplx"


@require_subclass(MachineVertex)
class AbstractSynapseExpandable(object, metaclass=AbstractBase):
    """ Indicates a class (a \
        :py:class:`~pacman.model.graphs.machine.MachineVertex`) \
        that has may need to run the SYNAPSE_EXPANDER aplx

    .. note::
        This is *not* implemented by the
        :py:class:`~.DelayExtensionMachineVertex`,
        which needs a different expander aplx
    """

    __slots__ = ()

    @abstractmethod
    def gen_on_machine(self):
        """ True if the synapses of a the slice of this vertex should be \
            generated on the machine.

        .. note::
            The typical implementation for this method will be to ask the
            app_vertex's synapse_manager

        :rtype: bool
        """

    @abstractproperty
    def connection_generator_region(self):
        """ The region containing the parameters of synaptic expansion

        :rtype: int

        :rtype: bool
        """

    @abstractmethod
    def read_generated_connection_holders(self, placement):
        """ Fill in the connection holders

        :param ~pacman.model.placements.Placement placement:
            Where the data is on the machine
        """

    @abstractproperty
    def max_gen_data(self):
        """ The maximum amount of synaptic data to be generated.  This
            is used to calculate the timeout of the execution.

        :rtype: int
        """

    @abstractproperty
    def bit_field_size(self):
        """ The amount of bit field data to be generated.  This is used to
            calculate the timeout of the execution.

        :rtype: int
        """
