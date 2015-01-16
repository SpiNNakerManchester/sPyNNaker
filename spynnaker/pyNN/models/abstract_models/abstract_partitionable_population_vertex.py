from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex


@add_metaclass(ABCMeta)
class AbstractPartitionablePopulationVertex(AbstractDataSpecableVertex,
                                            AbstractPartitionableVertex):

    def __init__(self, n_atoms, label, max_atoms_per_core, machine_time_step,
                 timescale_factor, constraints=None):
        AbstractDataSpecableVertex.__init__(
            self, n_atoms, label, machine_time_step=machine_time_step,
            timescale_factor=timescale_factor, constraints=constraints)
        AbstractPartitionableVertex.__init__(
            self, n_atoms, label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)

    def get_neuron_params_size(self, vertex_slice):
        """
        Gets the size of the neuron parameters for a range of neurons
        """
        return (constants.PARAMS_BASE_SIZE +
                (4 * ((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1)
                 * self._n_params))

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """
        Gets the SDRAM requirements for a range of atoms
        """

        # noinspection PyTypeChecker
        return (constants.SETUP_SIZE +
                self.get_neuron_params_size(vertex_slice)
                + self.get_synapse_parameter_size(vertex_slice)
                + self.get_stdp_parameter_size(
                    graph.incoming_edges_to_vertex(self))
                + constants.ROW_LEN_TABLE_SIZE
                + constants.MASTER_POPULATION_TABLE_SIZE
                + self.get_synaptic_blocks_memory_size(
                    vertex_slice, graph.incoming_edges_to_vertex(self))
                + self.get_spike_buffer_size(vertex_slice)
                + self.get_v_buffer_size(vertex_slice)
                + self.get_g_syn_buffer_size(vertex_slice))

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """
        Gets the DTCM requirements for a range of atoms
        """
        return (44 + (16 * 4)) * \
               ((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1)

    @abstractmethod
    def get_synapse_parameter_size(self, vertex_slice):
        """
        Gets the size of the synapse parameters for a given set of atoms
        """

    @abstractmethod
    def get_synaptic_blocks_memory_size(self, vertex_slice, in_edges):
        """
        Gets the memory size of the synapse blocks for a given set of atoms
        """

    @abstractmethod
    def get_stdp_parameter_size(self, in_edges):
        """
        Gets the size of the stdp parameters for a given set of atoms
        """

    @staticmethod
    @abstractmethod
    def set_model_max_atoms_per_core(new_value):
        """
        enforces other neural models to support model based max atoms contraints
        """

    # noinspection PyUnusedLocal
    def get_spike_buffer_size(self, vertex_slice):
        """
        Gets the size of the spike buffer for a range of neurons and time steps
        """
        if not self._record:
            return 0

        if self._no_machine_time_steps is None:
            return 0

        return self.get_recording_region_size(constants.OUT_SPIKE_BYTES)

    def get_v_buffer_size(self, vertex_slice):
        """
        Gets the size of the v buffer for a range of neurons and time steps
        """
        if not self._record_v:
            return 0
        size_per_time_step = \
            ((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1) *\
            constants.V_BUFFER_SIZE_PER_TICK_PER_NEURON
        return self.get_recording_region_size(size_per_time_step)

    def get_g_syn_buffer_size(self, vertex_slice):
        """
        Gets the size of the gsyn buffer for a range of neurons and time steps
        """
        if not self._record_gsyn:
            return 0

        size_per_time_step = \
            ((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1) * \
            constants.GSYN_BUFFER_SIZE_PER_TICK_PER_NEURON
        return self.get_recording_region_size(size_per_time_step)