import logging
from spynnaker.pyNN.models.neuron.connection_holder import ConnectionHolder

logger = logging.getLogger(__name__)


class SpYNNakerConnectionHolderGenerator(object):
    """
    method that sets up connection holders for reports to use.
    """

    def __call__(self, application_graph, graph_mapper):
        """
        :param application_graph:
        :param graph_mapper:
        :return:
        """

        data_holders = dict()
        for edge in application_graph.edges:

            # build connection holders
            connection_holder = ConnectionHolder(
                None, True, edge.pre_vertex.n_atoms,
                edge.post_vertex.n_atoms)

            # add pre run generators so that reports can extract without
            # going to machine.
            for synapse_information in edge.synapse_information:
                edge.post_vertex.add_pre_run_connection_holder(
                    connection_holder, edge, synapse_information)

                # store for the report generations
                data_holders[(edge, synapse_information)] = connection_holder

        # return the two holders
        return data_holders
