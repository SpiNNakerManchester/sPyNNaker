"""
"""
from spynnaker.pyNN.models.delay_extension.delay_extension_subvertex \
    import DelayExtensionSubvertex

# spinn front end common imports
from spinn_front_end_common.abstract_models\
    .abstract_provides_incoming_edge_constraints \
    import AbstractProvidesIncomingEdgeConstraints
from spinn_front_end_common.utilities import simulation_utilities
from spinn_front_end_common.interface.has_n_machine_timesteps \
    import HasNMachineTimesteps


# pacman imports
from pacman.model.constraints.partitioner_constraints.\
    partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_mask_constraint \
    import KeyAllocatorFixedMaskConstraint
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex

# general imports
import logging
import math

logger = logging.getLogger(__name__)


class DelayExtensionVertex(AbstractPartitionableVertex,
                           AbstractProvidesIncomingEdgeConstraints,
                           HasNMachineTimesteps):
    """ Provide delays to incoming spikes in multiples of the maximum delays \
        of a neuron (typically 16 or 32)
    """

    def __init__(self, n_keys, max_delay_per_neuron, source_vertex,
                 machine_time_step, timescale_factor, constraints=None,
                 label="DelayExtension"):
        """
        """

        AbstractPartitionableVertex.__init__(self, n_atoms=n_keys,
                                             constraints=constraints,
                                             label=label,
                                             max_atoms_per_core=256)
        AbstractProvidesIncomingEdgeConstraints.__init__(self)

        self._machine_time_step = machine_time_step
        self._time_scale_factor = timescale_factor
        self._max_delay_per_neuron = max_delay_per_neuron
        self._max_stages = 0
        self._source_vertex = source_vertex

        self.add_constraint(PartitionerSameSizeAsVertexConstraint(
            source_vertex))

    def get_incoming_edge_constraints(self, partitioned_edge, graph_mapper):
        """
        """
        return list([KeyAllocatorFixedMaskConstraint(0xFFFFF800)])

    @property
    def model_name(self):
        """
        """
        return "DelayExtension"

    @property
    def max_stages(self):
        """ The maximum number of delay stages required by any connection
            out of this delay extension vertex
        """
        return self._max_stages

    @max_stages.setter
    def max_stages(self, max_stages):
        """ Set the maximum number of delay stages
        """
        self._max_stages = max_stages

    @property
    def max_delay_per_neuron(self):
        """ The maximum delay handleable by neuron models
        """
        return self._max_delay_per_neuron

    # inherited from partitionable vertex
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """
        """
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return 128 * n_atoms

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """
        """

        n_atoms = vertex_slice.hi_atom - vertex_slice.lo_atom + 1
        block_len_words = int(math.ceil(n_atoms / 32.0))

        delay_params_sz = 4 * (self._DELAY_PARAMS_HEADER_WORDS +
                               (self._max_stages * block_len_words))

        return (simulation_utilities.HEADER_REGION_BYTES +
                delay_params_sz)

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """
        """
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return (44 + (16 * 4)) * n_atoms

    def create_subvertex(self, vertex_slice, resources_required, label=None,
                         constraints=None):
        return DelayExtensionSubvertex(
            resources_required, label, constraints, vertex_slice, self,
            self._machine_time_step, self._timescale_factor,
            self.n_machine_timesteps)
