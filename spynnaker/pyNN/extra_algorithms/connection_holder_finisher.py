from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spinn_utilities.progress_bar import ProgressBar


def finish_connection_holders(application_graph):
    """ Finishes the connection holders after data has been generated within
        them, allowing any waiting callbacks to be called
    """
    edges = application_graph.edges
    progress = ProgressBar(len(edges), "Finalising Retrieved Connections")
    for edge in progress.over(edges):
        if isinstance(edge, ProjectionApplicationEdge):
            for synapse_info in edge.synapse_information:
                synapse_info.finish_connection_holders()
