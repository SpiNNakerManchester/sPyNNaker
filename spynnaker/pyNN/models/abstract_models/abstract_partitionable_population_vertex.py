"""
AbstractPartitionablePopulationVertex
"""

# spynnaker imports
from spynnaker.pyNN.utilities import constants

# spinn front end imports
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex

# pacman imports
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex

# general imports
from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
import math


@add_metaclass(ABCMeta)
class AbstractPartitionablePopulationVertex(AbstractDataSpecableVertex,
                                            AbstractPartitionableVertex):
    """
    AbstractPartitionablePopulationVertex: provides functionality for the
    partitioner aglortihums for neural populations. such as:
    get_sdram usage
    """

    def __init__(self, n_atoms, label, max_atoms_per_core, machine_time_step,
                 timescale_factor, constraints=None):
        AbstractDataSpecableVertex.__init__(
            self, machine_time_step=machine_time_step,
            timescale_factor=timescale_factor)
        AbstractPartitionableVertex.__init__(
            self, n_atoms, label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)

    def get_neuron_params_size(self, vertex_slice):
        """
        Get the size of the neuron parameters for a range of neurons
        :param vertex_slice:
        :return:
        """

        # NOTE: Assumes 4-bytes per neuron parameter
        return (constants.POPULATION_NEURON_PARAMS_HEADER_BYTES +
                (4 * vertex_slice.n_atoms * self._n_params))

    def get_synapse_parameter_size(self, vertex_slice):
        """
        Get the size of the synapse parameters for a given set of atoms
        :param vertex_slice:
        :return:
        """

        # NOTE: Assumes 4-bytes per parameter
        # This is the size of the synapse shaping parameters
        #     (one per synapse type per neuron)
        # + the size of the ring buffer left shifts (one per synapse type)
        return ((4 * self.get_n_synapse_parameters_per_synapse_type() *
                 self.get_n_synapse_types() * vertex_slice.n_atoms) +
                (4 * self.get_n_synapse_types()))

    def get_spike_buffer_size(self, vertex_slice):
        """Get the size of the spike buffer for a range of neurons and
            time steps

        :param vertex_slice:
        :return:
        """
        if not self._record:
            return 0

        if self._no_machine_time_steps is None:
            return 0

        return self.get_recording_region_size(
            int(math.ceil(vertex_slice.n_atoms / 32.0)) * 4)

    def get_v_buffer_size(self, vertex_slice):
        """
        Gets the size of the v buffer for a range of neurons and time steps
        :param vertex_slice:
        :return:
        """
        if not self._record_v:
            return 0
        size_per_time_step = (vertex_slice.n_atoms *
                              constants.V_BUFFER_SIZE_PER_TICK_PER_NEURON)
        return self.get_recording_region_size(size_per_time_step)

    def get_g_syn_buffer_size(self, vertex_slice):
        """
        Gets the size of the gsyn buffer for a range of neurons and time steps
        :param vertex_slice:
        :return:
        """
        if not self._record_gsyn:
            return 0

        size_per_time_step = (vertex_slice.n_atoms *
                              constants.GSYN_BUFFER_SIZE_PER_TICK_PER_NEURON)
        return self.get_recording_region_size(size_per_time_step)

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """
        Gets the SDRAM requirements for a range of atoms
        :param vertex_slice:
        :param graph:
        :return:
        """
        in_edges = graph.incoming_edges_to_vertex(self)

        # noinspection PyTypeChecker
        return (constants.POPULATION_SYSTEM_REGION_BYTES +
                self.get_neuron_params_size(vertex_slice) +
                self.get_synapse_parameter_size(vertex_slice) +
                self.get_population_table_size(vertex_slice, in_edges) +
                self.get_synapse_dynamics_parameter_size(in_edges) +
                self.get_synaptic_blocks_memory_size(vertex_slice, in_edges) +
                self.get_spike_buffer_size(vertex_slice) +
                self.get_v_buffer_size(vertex_slice) +
                self.get_g_syn_buffer_size(vertex_slice))

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """
        Gets the DTCM requirements for a range of atoms
        :param vertex_slice:
        :param graph:
        :return:
        """
        return (44 + (16 * 4)) * \
               ((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1)

    @staticmethod
    @abstractmethod
    def set_model_max_atoms_per_core(new_value):
        """ enforce other neural models to support model based max atoms
            contraints
            :param new_value: setting of the model max atoms per core
        """

    @abstractmethod
    def get_n_synapse_parameters_per_synapse_type(self):
        """ Get the number of synapse parameters per synapse type per neuron
            (assumed to be 1 word each)
        """

    @abstractmethod
    def get_n_synapse_types(self):
        """ Get the number of synapse types"""

    @abstractmethod
    def get_population_table_size(self, vertex_slice, in_edges):
        """
        Get the size of a population table for a range of atoms
        :param vertex_slice:
        :param in_edges:
        :return:
        """

    @abstractmethod
    def get_synaptic_blocks_memory_size(self, vertex_slice, in_edges):
        """Get the memory size of the synapse blocks for a given set of atoms

        :param vertex_slice:
        :param in_edges:
        :return:
        """

    @abstractmethod
    def get_synapse_dynamics_parameter_size(self, in_edges):
        """
        Get the size of the synapse dynamics parameters for a given set
            of atoms
        :param in_edges:
        :return:
        """

    @abstractmethod
    def get_recording_region_size(self, bytes_per_timestep):
        """Get the size of a recording region given the number of bytes per
            timestep

        :param bytes_per_timestep:
        :return:
        """
