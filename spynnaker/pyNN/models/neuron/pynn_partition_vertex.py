from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.neuron import SynapticManager
from spynnaker.pyNN.models.abstract_models import (
    AbstractPopulationInitializable, AbstractPopulationSettable,
    AbstractReadParametersBeforeSet, AbstractContainsUnits)
from spynnaker.pyNN.utilities import constants

from spinn_front_end_common.abstract_models import \
    AbstractChangableAfterRun

from pacman.model.constraints.partitioner_constraints\
    import SameAtomsAsVertexConstraint
from pacman.model.graphs.application.application_edge \
    import ApplicationEdge


DEFAULT_MAX_ATOMS_PER_SYN_CORE = 64
SYN_CORES_PER_NEURON_CORE = 1
DEFAULT_MAX_ATOMS_PER_NEURON_CORE = DEFAULT_MAX_ATOMS_PER_SYN_CORE * SYN_CORES_PER_NEURON_CORE

# Hard-coded here, but to be moved outside as param
N_PARTITIONS = 2


class PyNNPartitionVertex(AbstractPopulationInitializable, AbstractPopulationSettable,
                          AbstractChangableAfterRun, AbstractReadParametersBeforeSet,
                          AbstractContainsUnits):

    __slots__ = [
        "_neuron_vertices",
        "_synapse_vertices",  # List of lists, each list corresponds to a neuron vertex
        "_n_atoms"]

    def __init__(self, n_neurons, label, constraints, max_atoms_neuron_core, spikes_per_second,
                 ring_buffer_sigma, neuron_model, pynn_model, incoming_spike_buffer_size):

        self._n_atoms = n_neurons

        self._neuron_vertices = list()
        self._synapse_vertices = list()

        for i in range(N_PARTITIONS):

            self._neuron_vertices.append(AbstractPopulationVertex(
                n_neurons/N_PARTITIONS, label + "_" + str(i) + "_neuron_vertex",
                constraints, max_atoms_neuron_core, spikes_per_second,
                ring_buffer_sigma, neuron_model, pynn_model))

            n_syn_types = self._neuron_vertices[i].get_n_synapse_types()

            syn_vertices = list()

            if constraints is None:

                syn_constraints = list()
            else:

                syn_constraints = constraints

            syn_constraints.append(SameAtomsAsVertexConstraint(self._neuron_vertices[i]))

            for index in range(n_syn_types):

                if n_syn_types > 1 and index == 0:

                    vertex = SynapticManager(1, 0, n_neurons, syn_constraints,
                                             label + "_" + str(i) + "_low_syn_vertex_" + str(index),
                                             max_atoms_neuron_core, neuron_model.get_global_weight_scale(),
                                             ring_buffer_sigma, spikes_per_second, incoming_spike_buffer_size,
                                             neuron_model.get_n_synapse_types())

                    vertex.connected_app_vertices = [self._neuron_vertices[i]]
                    syn_vertices.append(vertex)

                    vertex = SynapticManager(1, 0, n_neurons, syn_constraints,
                                             label + "_" + str(i) + "_high_syn_vertex_" + str(index),
                                             max_atoms_neuron_core, neuron_model.get_global_weight_scale(),
                                             ring_buffer_sigma, spikes_per_second, incoming_spike_buffer_size,
                                             neuron_model.get_n_synapse_types())

                    vertex.connected_app_vertices = [self._neuron_vertices[i]]
                    syn_vertices.append(vertex)

                else:

                    vertex = SynapticManager(1, index, n_neurons, syn_constraints,
                                             label + "_" + str(i) + "_syn_vertex_" + str(index),
                                             max_atoms_neuron_core, neuron_model.get_global_weight_scale(),
                                             ring_buffer_sigma, spikes_per_second, incoming_spike_buffer_size,
                                             neuron_model.get_n_synapse_types())

                    vertex.connected_app_vertices = [self._neuron_vertices[i]]
                    syn_vertices.append(vertex)

            self._neuron_vertices[i].connected_app_vertices = syn_vertices
            self._synapse_vertices.append(syn_vertices)

    def get_application_vertices(self):

        vertices = [self._neuron_vertices]
        vertices.extend(self._synapse_vertices)

        return vertices

    @property
    def out_vertices(self):
        return self._neuron_vertices

    @property
    def in_vertices(self):
        return self._synapse_vertices

    @property
    def n_atoms(self):
        return self._n_atoms

    def add_internal_edges_and_vertices(self, spinnaker_control):

        for i in range(N_PARTITIONS):

            spinnaker_control.add_application_vertex(self._neuron_vertices[i])

            for vertex in self._synapse_vertices[i]:

                spinnaker_control.add_application_vertex(vertex)
                spinnaker_control.add_application_edge(ApplicationEdge(
                    vertex, self._neuron_vertices[i],
                    label="internal_edge {}".format(spinnaker_control.none_labelled_edge_count)),
                    constants.SPIKE_PARTITION_ID)
                spinnaker_control.increment_none_labelled_edge_count()

    @property
    def conductance_based(self):
        return self._neuron_vertices[0].conductance_based

    def initialize(self, variable, value):
        for i in range(N_PARTITIONS):
            self._neuron_vertices[i].initialize(variable, value)

    # THINK PARAMS ARE THE SAME FOR BOTH THE APP VERTICES!!!!!!!
    def get_value(self, key):
        return self._neuron_vertices[0].get_value(key)

    def set_value(self, key, value):
        for i in range(N_PARTITIONS):
            self._neuron_vertices[i].set_value(key, value)

    def read_parameters_from_machine(self, globals_variables):

        for i in range(N_PARTITIONS):
            machine_vertices = globals_variables.get_simulator().graph_mapper \
                .get_machine_vertices(self._neuron_vertices[i])

            # go through each machine vertex and read the neuron parameters
            # it contains
            for machine_vertex in machine_vertices:
                # tell the core to rewrite neuron params back to the
                # SDRAM space.
                placement = globals_variables.get_simulator().placements. \
                    get_placement_of_vertex(machine_vertex)

                self.neuron_vertices[i].read_parameters_from_machine(
                    globals_variables.get_simulator().transceiver, placement,
                    globals_variables.get_simulator().graph_mapper.get_slice(
                        machine_vertex))

    @property
    def n_atoms(self):
        return self._n_atoms

    def get_units(self, variable):
        return self._neuron_vertices[0].get_units(variable)

    def mark_no_changes(self):
        for i in range(N_PARTITIONS):
            self._neuron_vertices[i].mark_no_changes()

    @property
    def requires_mapping(self):
        return self._neuron_vertices[0].requires_mapping()

    def set_initial_value(self, variable, value, selector=None):
        for i in range(N_PARTITIONS):
            self._neuron_vertices[i].set_initial_value(variable, value, selector)

    # SHOULD BE THE SAME FOR BOTH THE VERTICES!!!!s
    def get_initial_value(self, variable, selector=None):
        return self._neuron_vertices[0].get_initial_value(variable, selector)

    @property
    def initialize_parameters(self):
        return self._neuron_vertices[0].initialize_parameters

    def get_synapse_id_by_target(self, target):
        self._neuron_vertices[0].get_synapse_id_by_target(target)

    def set_synapse_dynamics(self, synapse_dynamics):
        for vertex_list in self._synapse_vertices:
            for vertex in vertex_list:
                vertex.set_synapse_dynamics(synapse_dynamics)

    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        return self._synapse_vertices[0][0].\
            get_maximum_delay_supported_in_ms(machine_time_step)
