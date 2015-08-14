"""
"""

# spynnaker imports
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.neuron.abstract_population_recordable_vertex \
    import AbstractPopulationRecordableVertex

# pacman imports
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex

# general imports
from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
import math


@add_metaclass(ABCMeta)
class AbstractPartitionablePopulationVertex(
        AbstractPartitionableVertex, AbstractPopulationRecordableVertex):
    """ A partitionable vertex for neuron models
    """

    def __init__(self, n_neurons, label, max_atoms_per_core, machine_time_step,
                 timescale_factor, n_params, constraints=None):
        """

        :param n_neurons: The number of neurons in the population
        :param label: The label of the population
        :param max_atoms_per_core: The absolute maximum number of atoms to be\
                run on any core
        :param machine_time_step: The number of microseconds per timestep
        :param timescale_factor: The multiplier by which the machine is slowed\
                down
        :param n_params: The number of parameters in the neuron model
        """
        AbstractPartitionableVertex.__init__(
            self, n_neurons, label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)
        AbstractPopulationRecordableVertex.__init__(
            self, label, machine_time_step)
        self._n_params = n_params

    def get_neuron_params_region_size(self, vertex_slice):
        """ Get the size of the neuron parameters region
        """

        # NOTE: Assumes 4-bytes per neuron parameter
        return (constants.POPULATION_NEURON_PARAMS_HEADER_BYTES +
                (4 * vertex_slice.n_atoms * self._n_params))

    def get_synapse_params_region_size(self, vertex_slice):
        """ Get the size of the synapse parameters region
        """

        # NOTE: Assumes 4-bytes per parameter
        # This is the size of the synapse shaping parameters
        #     (one per synapse type per neuron)
        # + the size of the ring buffer left shifts (one per synapse type)
        return ((4 * self.get_n_synapse_parameters_per_synapse_type() *
                 self.get_n_synapse_types() * vertex_slice.n_atoms) +
                (4 * self.get_n_synapse_types()))

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """
        Gets the SDRAM requirements for a range of atoms
        :param vertex_slice:
        :param graph:
        :return:
        """
        in_edges = graph.incoming_edges_to_vertex(self)

        # noinspection PyTypeChecker
        value = (common_constants.TIMINGS_REGION_BYTES +
                 len(self._get_components_magic_numbers()) * 4 +
                 (1 + constants.N_POPULATION_RECORDING_REGIONS) * 4 +
                 self.get_neuron_params_size(vertex_slice) +
                 self.get_synapse_parameter_size(vertex_slice) +
                 self.get_population_table_size(vertex_slice, in_edges) +
                 self.get_synapse_dynamics_parameter_size(in_edges) +
                 self.get_synaptic_blocks_memory_size(vertex_slice, in_edges) +
                 self.get_spike_buffer_size(vertex_slice) +
                 self.get_v_buffer_size(vertex_slice) +
                 self.get_g_syn_buffer_size(vertex_slice))
        return math.ceil(value)

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
