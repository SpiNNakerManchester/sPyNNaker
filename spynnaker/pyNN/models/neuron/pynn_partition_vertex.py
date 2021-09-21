import numpy as np
import math

from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.neuron import SynapticManager
from spynnaker.pyNN.models.abstract_models import (
    AbstractPopulationInitializable, AbstractPopulationSettable,
    AbstractReadParametersBeforeSet, AbstractContainsUnits,
    AbstractAcceptsIncomingSynapses)
from spynnaker.pyNN.models.common import (
    AbstractSpikeRecordable, AbstractNeuronRecordable,
    AbstractSynapseRecordable)
from spynnaker.pyNN.utilities import constants

from spinn_front_end_common.abstract_models import \
    AbstractChangableAfterRun

from pacman.model.constraints.partitioner_constraints\
    import SameAtomsAsVertexConstraint
from pacman.model.graphs.application.application_edge \
    import ApplicationEdge

from spinn_utilities.overrides import overrides

# Exported for higher level control:
# DEFAULT_MAX_ATOMS_PER_SYN_CORE = 64
# SYN_CORES_PER_NEURON_CORE = 1
# DEFAULT_MAX_ATOMS_PER_NEURON_CORE = DEFAULT_MAX_ATOMS_PER_SYN_CORE * SYN_CORES_PER_NEURON_CORE


class PyNNPartitionVertex(AbstractPopulationInitializable, AbstractPopulationSettable,
                          AbstractChangableAfterRun, AbstractReadParametersBeforeSet,
                          AbstractContainsUnits, AbstractSpikeRecordable,
                          AbstractNeuronRecordable, AbstractSynapseRecordable):

    __slots__ = [
        "_neuron_vertices",
        "_synapse_vertices",  # List of lists, each list corresponds to a neuron vertex
        "_n_atoms",
        "_n_syn_types",
        "_neurons_partition",
        "_n_outgoing_partitions",
        "_n_incoming_partitions",
        "_max_atoms_neuron_core"]

    def __init__(self, n_neurons, label, constraints, max_atoms_neuron_core, spikes_per_second,
                 ring_buffer_sigma, neuron_model, pynn_model, incoming_spike_buffer_size,
                 incoming_partitions, outgoing_partitions):

        self._n_atoms = n_neurons

        self._n_incoming_partitions = incoming_partitions

        self._max_atoms_neuron_core = max_atoms_neuron_core

        self._n_outgoing_partitions = 1 if self._n_atoms <= self._max_atoms_neuron_core else outgoing_partitions #int(math.ceil(float(self._n_atoms) / self._max_atoms_neuron_core))

        self._neuron_vertices = list()
        self._synapse_vertices = list()
        self._n_syn_types = neuron_model.get_n_synapse_types()

        if len(self._n_incoming_partitions) < self._n_syn_types:
            raise Exception("Incorrect number of incoming partitions."
                            " Each synapse type must have at least 1 incoming partition.")

        self._neurons_partition = self._compute_partition_and_offset_size()

        offset = 0

        for i in range(self._n_outgoing_partitions):

            # Distribute neurons in order to have the low neuron cores completely filled
            #atoms = self._offset if (self._n_atoms - (self._offset * (i + 1)) >= 0) \
            #    else self._n_atoms - (self._offset * i)

            self._neuron_vertices.append(AbstractPopulationVertex(
                self._neurons_partition[i], offset, label + "_" + str(i) + "_neuron_vertex",
                constraints, max_atoms_neuron_core, spikes_per_second,
                ring_buffer_sigma, neuron_model, pynn_model))

            syn_vertices = list()

            if constraints is None:

                syn_constraints = list()
            else:

                syn_constraints = constraints

            syn_constraints.append(SameAtomsAsVertexConstraint(self._neuron_vertices[i]))

            # memory offset for the synaptic contributions
            mem_offset = 0

            for index in range(self._n_syn_types):

                for j in range(self._n_incoming_partitions[index]):

                    vertex = SynapticManager(1, index, self._neurons_partition[i], offset, syn_constraints,
                                            label + "_p" + str(i) + "_v" + str(j) + "_syn_type_" + str(index),
                                            max_atoms_neuron_core, neuron_model.get_global_weight_scale(),
                                            ring_buffer_sigma, spikes_per_second, incoming_spike_buffer_size,
                                            self._n_syn_types, mem_offset)

                    vertex.connected_app_vertices = [self._neuron_vertices[i]]
                    syn_vertices.append(vertex)

                    mem_offset += 1

                # Ensures correct memory alignment for the synaptic contributions in case
                # some synapse types are not used in the simulation
                if self._n_incoming_partitions[index] == 0:
                    mem_offset += 1

            self._neuron_vertices[i].incoming_partitions = self._n_incoming_partitions

            self._neuron_vertices[i].connected_app_vertices = syn_vertices
            self._synapse_vertices.append(syn_vertices)

            offset += self._neurons_partition[i]

        for syn_index in range(len(self._synapse_vertices[0])):

            slice_list = list()
            for i in range(self._n_outgoing_partitions):

                slice_list.append(self._synapse_vertices[i][syn_index])

            for i in range(self._n_outgoing_partitions):

                self._synapse_vertices[i][syn_index].slice_list = slice_list

        for i in range(self._n_outgoing_partitions):
            self._neuron_vertices[i].slice_list = self._neuron_vertices

    def _compute_outgoing_partitions(self):
        return int(math.ceil(float(self._n_atoms) / self._max_atoms_neuron_core))

    def _compute_partition_and_offset_size(self):

        min_neurons_per_partition = int(math.floor((self._n_atoms / self._n_outgoing_partitions) / self._max_atoms_neuron_core) * self._max_atoms_neuron_core)

        remaining_neurons = self._n_atoms - (min_neurons_per_partition * self._n_outgoing_partitions)

        contents = [min_neurons_per_partition for i in range(self._n_outgoing_partitions)]
        for i in range(self._n_outgoing_partitions):
            if remaining_neurons - self._max_atoms_neuron_core >= 0:
                remaining_neurons -= self._max_atoms_neuron_core
                contents[i] += self._max_atoms_neuron_core
            else:
                contents[self._n_outgoing_partitions - 1] += remaining_neurons
                break
        return contents

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

    @property
    def n_syn_types(self):
        return self._n_syn_types

    @property
    def n_incoming_partitions(self):
        return self._n_incoming_partitions

    def add_internal_edges_and_vertices(self, spinnaker_control):

        for i in range(self._n_outgoing_partitions):

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
        for i in range(self._n_outgoing_partitions):
            self._neuron_vertices[i].initialize(variable, value)

    # THINK PARAMS ARE THE SAME FOR BOTH THE APP VERTICES!!!!!!!
    def get_value(self, key):
        return self._neuron_vertices[0].get_value(key)

    def set_value(self, key, value):
        for i in range(self._n_outgoing_partitions):
            self._neuron_vertices[i].set_value(key, value)

    def read_parameters_from_machine(self, globals_variables):

        for i in range(self._n_outgoing_partitions):
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

    def get_units(self, variable):
        if variable == 'synapse':
            return self._synapse_vertices[0][0].get_units(variable)
        return self._neuron_vertices[0].get_units(variable)

    def mark_no_changes(self):
        for i in range(self._n_outgoing_partitions):
            self._neuron_vertices[i].mark_no_changes()

    @property
    def requires_mapping(self):
        return self._neuron_vertices[0].requires_mapping()

    def set_initial_value(self, variable, value, selector=None):

        offset = 0
        j = 0

        if selector is None:
            sel = None

        for i in range(self._n_outgoing_partitions):

            if selector is not None:

                sel = []

                while j < len(selector) and selector[j] < self._neuron_vertices[i].n_atoms + offset:
                    sel.append(selector[j] - offset)
                    j += 1

            self._neuron_vertices[i].set_initial_value(variable, value, sel)

            offset += self._neurons_partition[i]

    # SHOULD BE THE SAME FOR ALL THE VERTICES!!!!
    def get_initial_value(self, variable, selector=None):
        return self._neuron_vertices[0].get_initial_value(variable, selector)

    @property
    def initialize_parameters(self):
        return self._neuron_vertices[0].initialize_parameters

    def get_synapse_id_by_target(self, target):
        return self._neuron_vertices[0].get_synapse_id_by_target(target)

    def set_synapse_dynamics(self, synapse_dynamics, synapse_type):

        offset = 0
        vertices = self._n_incoming_partitions[synapse_type]
        for i in range(synapse_type):
            offset += self._n_incoming_partitions[i]

        for out_partition in self._synapse_vertices:
            for i in range(offset, offset + vertices):
                out_partition[i].set_synapse_dynamics(synapse_dynamics, synapse_type)

    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        return self._synapse_vertices[0][0].\
            get_maximum_delay_supported_in_ms(machine_time_step)

    def clear_connection_cache(self):
        for partition in self._synapse_vertices:
            for vertex in partition:
                vertex.clear_connection_cache()

    def get_max_atoms_per_core(self):
        return self._max_atoms_neuron_core

    def describe(self):
        # Correct??
        return self._neuron_vertices[0].describe()

    @overrides(
        AbstractNeuronRecordable.clear_recording)
    def clear_recording(
            self, variable, buffer_manager, placements, graph_mapper):
        for vertex in self._neuron_vertices:
            vertex.clear_recording(variable, buffer_manager, placements, graph_mapper)

    @overrides(
        AbstractSpikeRecordable.clear_spike_recording)
    def clear_spike_recording(self, buffer_manager, placements, graph_mapper):
        for vertex in self._neuron_vertices:
            vertex.clear_spike_recording(buffer_manager, placements, graph_mapper)

    @overrides(
        AbstractSynapseRecordable.clear_synapse_recording)
    def clear_synapse_recording(self, variable, buffer_manager, placements,
                                graph_mapper):
        for partition in self._synapse_vertices:
            for vertex in partition:
                vertex.clear_synapse_recording(
                    variable, buffer_manager, placements, graph_mapper)

    @overrides(AbstractNeuronRecordable.is_recording)
    def is_recording(self, variable):
        return self._neuron_vertices[0].is_recording(variable)

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self._neuron_vertices[0].is_recording_spikes()

    @overrides(AbstractSynapseRecordable.is_recording_synapses)
    def is_recording_synapses(self, variable):
        return self._synapse_vertices[0][0].is_recording_synapses(variable)

    @overrides(AbstractNeuronRecordable.set_recording)
    def set_recording(self, variable, new_state=True, sampling_interval=None,
                      indexes=None):
        for vertex in self._neuron_vertices:
            vertex.set_recording(variable, new_state, sampling_interval, indexes)

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        for vertex in self._neuron_vertices:
            vertex.set_recording_spikes(new_state, sampling_interval, indexes)

    @overrides(AbstractSynapseRecordable.set_synapse_recording)
    def set_synapse_recording(self, variable, new_state=True, sampling_interval=None,
                      indexes=None):
        for partition in self._synapse_vertices:
            for vertex in partition:
                vertex.set_synapse_recording(
                    variable, new_state, sampling_interval, indexes)

    @overrides(AbstractNeuronRecordable.get_recordable_variables)
    def get_recordable_variables(self):
        return self._neuron_vertices[0].get_recordable_variables()

    @overrides(AbstractSynapseRecordable.get_synapse_recordable_variables)
    def get_synapse_recordable_variables(self):
        return self._synapse_vertices[0][0].get_synapse_recordable_variables()

    @overrides(AbstractNeuronRecordable.get_neuron_sampling_interval)
    def get_neuron_sampling_interval(self, variable):
        return self._neuron_vertices[0].get_neuron_sampling_interval(variable)

    @overrides(AbstractSpikeRecordable.get_spikes_sampling_interval)
    def get_spikes_sampling_interval(self):
        return self._neuron_vertices[0].get_spikes_sampling_interval()

    @overrides(AbstractSynapseRecordable.get_synapse_sampling_interval)
    def get_synapse_sampling_interval(self, variable):
        return self._synapse_vertices[0][0].\
            get_synapse_sampling_interval(variable)

    @overrides(AbstractNeuronRecordable.get_data)
    def get_data(self, variable, n_machine_time_steps, placements,
                 graph_mapper, buffer_manager, machine_time_step):
        values = list()
        for vertex in self._neuron_vertices:
            values.append(vertex.get_data(
                variable, n_machine_time_steps, placements, graph_mapper,
                buffer_manager, machine_time_step))

        sampling_interval = values[0][2]
        indexes = values[0][1]
        data = values[0][0]

        for index in range(1, len(values)):
            indexes.extend(values[index][1])
            data = np.append(data, values[index][0], axis=1)

        return (data, indexes, sampling_interval)

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(
            self, placements, graph_mapper, buffer_manager, machine_time_step):
        spikes = list()
        for vertex in self._neuron_vertices:
            spikes.append(vertex.get_spikes(placements, graph_mapper, buffer_manager, machine_time_step))

        res = spikes[0]
        for index in range(1, len(spikes)):
            res = np.append(res, spikes[index], axis=0)

        return res

    @overrides(AbstractSynapseRecordable.get_synapse_data)
    def get_synapse_data(self, variable, n_machine_time_steps, placements,
                 graph_mapper, buffer_manager, machine_time_step):
        in_spikes = dict()

        for vertex in range(len(self._synapse_vertices[0])):
            for partition in range(len(self._synapse_vertices)):
                (data, index, sampling_interval) = self._synapse_vertices[partition][vertex].\
                                 get_synapse_data(variable, n_machine_time_steps, placements,
                                                  graph_mapper, buffer_manager, machine_time_step)
                in_spikes.update(data)

        return (in_spikes, index, sampling_interval)


    # def add_pre_run_connection_holder(
    #         self, connection_holder, projection_edge, synapse_information):
    #
    #     for vertex_list in self._synapse_vertices:
    #         for vertex in vertex_list:
    #             vertex.add_pre_run_connection_holder(
    #                 connection_holder, projection_edge, synapse_information)
    #
    # # List of the connections, one per syn vertex
    # def get_connections_from_machine(self, transceiver, placement, machine_edge, graph_mapper,
    #                                  routing_infos, synapse_info, machine_time_step,
    #                                  using_extra_monitor_cores, placements=None, data_receiver=None,
    #                                  sender_extra_monitor_core_placement=None,
    #                                  extra_monitor_cores_for_router_timeout=None,
    #                                  handle_time_out_configuration=True, fixed_routes=None):
    #     connections = list()
    #     for vertex_list in self._synapse_vertices:
    #         for vertex in vertex_list:
    #             connections.append(vertex.get_connections_from_machine(
    #                 transceiver, placement, machine_edge, graph_mapper,
    #                 routing_infos, synapse_info, machine_time_step,
    #                 using_extra_monitor_cores, placements, data_receiver,
    #                 sender_extra_monitor_core_placement,
    #                 extra_monitor_cores_for_router_timeout,
    #                 handle_time_out_configuration, fixed_routes))