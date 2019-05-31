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


class PyNNPartitionVertex(AbstractPopulationInitializable, AbstractPopulationSettable,
                          AbstractChangableAfterRun, AbstractReadParametersBeforeSet,
                          AbstractContainsUnits):

    __slots__ = [
        "_neuron_vertices",
        "_synapse_vertices",
        "_n_atoms"]

    def __init__(self, n_neurons, label, constraints, max_atoms_neuron_core, spikes_per_second,
                 ring_buffer_sigma, neuron_model, pynn_model, incoming_spike_buffer_size):

        self._n_atoms = n_neurons

        self._neuron_vertices = list()

        self._neuron_vertices.append(AbstractPopulationVertex(
            n_neurons, label + "_" + str(self._partition_index) + "_neuron_vertex",
            constraints, max_atoms_neuron_core, spikes_per_second,
            ring_buffer_sigma, neuron_model, pynn_model))

        self._synapse_vertices = list()

        if constraints is None:

            syn_constraints = list()
        else:

            syn_constraints = constraints

        syn_constraints.append(SameAtomsAsVertexConstraint(self._neuron_vertices))

        n_syn_types = self._neuron_vertices.get_n_synapse_types()

        for index in range(n_syn_types):

            if n_syn_types > 1 and index == 0:

                vertex = SynapticManager(1, 0, n_neurons, syn_constraints,
                                         label + "_" + str(self._partition_index) + "_low_syn_vertex_" + str(index),
                                         max_atoms_neuron_core, neuron_model.get_global_weight_scale(),
                                         ring_buffer_sigma, spikes_per_second, incoming_spike_buffer_size,
                                         neuron_model.get_n_synapse_types())

                vertex.connected_app_vertices = [self._neuron_vertices]
                self._synapse_vertices.append(vertex)

                vertex = SynapticManager(1, 0, n_neurons, syn_constraints,
                                         label + "_" + str(self._partition_index) + "_high_syn_vertex_" + str(index),
                                         max_atoms_neuron_core, neuron_model.get_global_weight_scale(),
                                         ring_buffer_sigma, spikes_per_second, incoming_spike_buffer_size,
                                         neuron_model.get_n_synapse_types())

                vertex.connected_app_vertices = [self._neuron_vertices]
                self._synapse_vertices.append(vertex)
            else:

                vertex = SynapticManager(1, index, n_neurons, syn_constraints,
                                         label + "_" + str(self._partition_index) + "_syn_vertex_" + str(index),
                                         max_atoms_neuron_core, neuron_model.get_global_weight_scale(),
                                         ring_buffer_sigma, spikes_per_second, incoming_spike_buffer_size,
                                         neuron_model.get_n_synapse_types())

                vertex.connected_app_vertices = [self._neuron_vertices]
                self._synapse_vertices.append(vertex)

        self._neuron_vertices.connected_app_vertices = self._synapse_vertices

    def get_application_vertices(self):

        vertices = [self._neuron_vertices]
        vertices.extend(self._synapse_vertices)

        return vertices

    @property
    def neuron_vertex(self):
        return self._neuron_vertices

    @property
    def synapse_vertices(self):
        return self._synapse_vertices

    @property
    def n_atoms(self):
        return self._n_atoms

    def add_internal_edges_and_vertices(self, spinnaker_control):

        spinnaker_control.add_application_vertex(self._neuron_vertices)

        for index in range(len(self._synapse_vertices)):

            spinnaker_control.add_application_vertex(self._synapse_vertices[index])
            spinnaker_control.add_application_edge(ApplicationEdge(
                self._synapse_vertices[index], self._neuron_vertices,
                label="internal_edge {}".format(spinnaker_control.none_labelled_edge_count)),
                constants.SPIKE_PARTITION_ID)
            spinnaker_control.increment_none_labelled_edge_count()
