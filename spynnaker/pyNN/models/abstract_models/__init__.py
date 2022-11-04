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

from .abstract_accepts_incoming_synapses import AbstractAcceptsIncomingSynapses
from .abstract_has_delay_stages import AbstractHasDelayStages
from .abstract_max_spikes import AbstractMaxSpikes
from .abstract_synapse_expandable import (
    AbstractSynapseExpandable, SYNAPSE_EXPANDER_APLX)
from .sends_synaptic_inputs_over_sdram import SendsSynapticInputsOverSDRAM
from .receives_synaptic_inputs_over_sdram import (
    ReceivesSynapticInputsOverSDRAM)
from .has_synapses import HasSynapses
from .abstract_neuron_expandable import (
    AbstractNeuronExpandable, NEURON_EXPANDER_APLX)
from .parameter_holder import ParameterHolder
from .population_application_vertex import (
    PopulationApplicationVertex, RecordingType)
from .population_fpga_vertex import PopulationFPGAVertex
from .population_spinnaker_link_vertex import PopulationSpiNNakerLinkVertex
from .population_2d_fpga_vertex import Population2DFPGAVertex
from .supports_structure import SupportsStructure
from .has_shape_key_fields import HasShapeKeyFields

__all__ = ["AbstractAcceptsIncomingSynapses", "AbstractHasDelayStages",
           "AbstractMaxSpikes", "AbstractSynapseExpandable",
           "SYNAPSE_EXPANDER_APLX",
           "SendsSynapticInputsOverSDRAM", "ReceivesSynapticInputsOverSDRAM",
           "HasSynapses", "AbstractNeuronExpandable", "NEURON_EXPANDER_APLX",
           "ParameterHolder", "PopulationApplicationVertex", "RecordingType",
           "PopulationFPGAVertex", "PopulationSpiNNakerLinkVertex",
           "Population2DFPGAVertex", "SupportsStructure", "HasShapeKeyFields"]
