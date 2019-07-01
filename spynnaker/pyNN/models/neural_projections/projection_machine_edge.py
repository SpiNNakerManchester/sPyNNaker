from pacman.model.partitioner_interfaces.abstract_controls_destination_of_edges import \
    AbstractControlsDestinationOfEdges
from pacman.model.partitioner_interfaces.abstract_controls_source_of_edges import \
    AbstractControlsSourceOfEdges
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.utilities import utility_calls
from pacman.model.graphs.machine import MachineEdge
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.interface.provenance import (
    AbstractProvidesLocalProvenanceData)
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector, FromListConnector)
from spynnaker.pyNN.models.abstract_models import (
    AbstractWeightUpdatable, AbstractFilterableEdge)
from spinnak_ear.spinnak_ear_machine_vertices.drnl_machine_vertex import \
    DRNLMachineVertex


class ProjectionMachineEdge(
        MachineEdge, AbstractFilterableEdge,
        AbstractWeightUpdatable, AbstractProvidesLocalProvenanceData):
    __slots__ = [
        "__synapse_information"]

    def __init__(
            self, synapse_information, pre_vertex, post_vertex,
            label=None, traffic_weight=1):
        # pylint: disable=too-many-arguments
        super(ProjectionMachineEdge, self).__init__(
            pre_vertex, post_vertex, label=label,
            traffic_weight=traffic_weight)

        self.__synapse_information = synapse_information

    @property
    def synapse_information(self):
        return self.__synapse_information

    @overrides(AbstractFilterableEdge.filter_edge)
    def filter_edge(self, graph_mapper):
        # Filter one-to-one connections that are out of range
        # Note: there may be other connectors stored on the same edge!

        pre_app_vertex = graph_mapper.get_application_vertex(self.pre_vertex)
        post_app_vertex = graph_mapper.get_application_vertex(self.post_vertex)
        n_filtered = 0
        for synapse_info in self.__synapse_information:
            # process pre atoms
            if isinstance(pre_app_vertex, AbstractControlsSourceOfEdges):
                machine_slice = pre_app_vertex.get_pre_slice_for(
                    self.pre_vertex)
                pre_lo = machine_slice.lo_atom
                pre_hi = machine_slice.hi_atom
            else:
                pre_lo = graph_mapper.get_slice(self.pre_vertex).lo_atom
                pre_hi = graph_mapper.get_slice(self.pre_vertex).hi_atom

            # process post atoms
            if isinstance(post_app_vertex, AbstractControlsDestinationOfEdges):
                machine_slice = post_app_vertex.get_post_slice_for(
                    self.post_vertex)
                post_lo = machine_slice.lo_atom
                post_hi = machine_slice.hi_atom
            else:
                post_lo = graph_mapper.get_slice(self.post_vertex).lo_atom
                post_hi = graph_mapper.get_slice(self.post_vertex).hi_atom

            # handle the different connectors
            if isinstance(synapse_info.connector, OneToOneConnector):
                if pre_hi < post_lo or pre_lo > post_hi:
                    n_filtered += 1
                return n_filtered == len(self._synapse_information)
            elif isinstance(synapse_info.connector, FromListConnector):
                if synapse_info.connector.conn_matrix is None:
                    return False
                array = synapse_info.connector.conn_matrix[
                        pre_lo:pre_hi + 1, post_lo:post_hi + 1]
                if len(array[0]) == 0:
                    return True
                if array.max() > 0:
                    return False
                return True
        return False

    @overrides(AbstractWeightUpdatable.update_weight)
    def update_weight(self, graph_mapper):
        pre_vertex = graph_mapper.get_application_vertex(
            self.pre_vertex)
        pre_vertex_slice = graph_mapper.get_slice(
            self.pre_vertex)

        weight = 0
        for synapse_info in self.__synapse_information:
            new_weight = synapse_info.connector.\
                get_n_connections_to_post_vertex_maximum()
            new_weight *= pre_vertex_slice.n_atoms
            if hasattr(pre_vertex, "rate"):
                rate = pre_vertex.rate
                if hasattr(rate, "__getitem__"):
                    rate = max(rate)
                elif globals_variables.get_simulator().is_a_pynn_random(rate):
                    rate = utility_calls.get_maximum_probable_value(
                        rate, pre_vertex_slice.n_atoms)
                new_weight *= rate
            elif hasattr(pre_vertex, "spikes_per_second"):
                new_weight *= pre_vertex.spikes_per_second
            weight += new_weight

        self._traffic_weight = weight

    @overrides(AbstractProvidesLocalProvenanceData.get_local_provenance_data)
    def get_local_provenance_data(self):
        prov_items = list()
        for synapse_info in self.__synapse_information:
            prov_items.extend(
                synapse_info.connector.get_provenance_data())
            prov_items.extend(
                synapse_info.synapse_dynamics.get_provenance_data(
                    self.pre_vertex.label, self.post_vertex.label))
        return prov_items
