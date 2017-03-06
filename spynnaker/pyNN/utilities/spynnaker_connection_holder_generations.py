import logging
from spinn_machine.utilities.progress_bar import ProgressBar
from spynnaker.pyNN.models.neuron.connection_holder import ConnectionHolder
from spynnaker.pyNN.models.neural_projections.projection_application_edge \
    import ProjectionApplicationEdge

logger = logging.getLogger(__name__)


class SpYNNakerConnectionHolderGenerator(object):
    """
    method that sets up connection holders for reports to use.
    """

    def __call__(self, application_graph):
        """
        :param application_graph: app graph
        :return: the set of connection holders for after dsg generation
        """

        progress_bar = ProgressBar(
            application_graph.n_outgoing_edge_partitions,
            "Generating connection holders for reporting connection data.")

        data_holders = dict()
        for partition in application_graph.outgoing_edge_partitions:
            for edge in partition.edges:

                # add pre run generators so that reports can extract without
                # going to machine.
                if isinstance(edge, ProjectionApplicationEdge):

                    # build connection holders
                    connection_holder = ConnectionHolder(
                        None, True, edge.pre_vertex.n_atoms,
                        edge.post_vertex.n_atoms)

                    for synapse_information in edge.synapse_information:
                        edge.post_vertex.add_pre_run_connection_holder(
                            connection_holder, edge, synapse_information)

                        # store for the report generations
                        data_holders[(edge, synapse_information)] = \
                            connection_holder
            progress_bar.update()
        progress_bar.end()

        # return the two holders
        return data_holders
