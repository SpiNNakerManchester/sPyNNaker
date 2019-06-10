from spinn_utilities.overrides import overrides
from spynnaker.pyNN.utilities import utility_calls
from pacman.model.graphs.machine import MachineEdge
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.interface.provenance import (
    AbstractProvidesLocalProvenanceData)
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector)
from spynnaker.pyNN.models.abstract_models import (
    AbstractWeightUpdatable, AbstractFilterableEdge)


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
        n_filtered = 0
        for synapse_info in self.__synapse_information:
            if isinstance(synapse_info.connector, OneToOneConnector):
                pre_lo = graph_mapper.get_slice(self.pre_vertex).lo_atom
                pre_hi = graph_mapper.get_slice(self.pre_vertex).hi_atom
                post_lo = graph_mapper.get_slice(self.post_vertex).lo_atom
                post_hi = graph_mapper.get_slice(self.post_vertex).hi_atom
                if pre_hi < post_lo or pre_lo > post_hi:
                    n_filtered += 1

        return (n_filtered == len(self.__synapse_information))

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
