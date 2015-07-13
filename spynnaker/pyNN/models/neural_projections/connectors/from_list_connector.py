from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_properties.synapse_row_info \
    import SynapseRowInfo
import logging
import numpy

logger = logging.getLogger(__name__)


class FromListConnector(AbstractConnector):
    """
    Make connections according to a list.

    :param `list` conn_list:
        a list of tuples, one tuple for each connection. Each
        tuple should contain::

         (pre_idx, post_idx, weight, delay)

        where pre_idx is the index (i.e. order in the Population,
        not the ID) of the presynaptic neuron, and post_idx is
        the index of the postsynaptic neuron.
    """

    def __init__(self, conn_list=None, safe=True, verbose=False):
        """
        Creates a new FromListConnector.
        """
        if not safe:
            logger.warn("the modification of the safe parameter will be "
                        "ignored")
        if verbose:
            logger.warn("the modification of the verbose parameter will be "
                        "ignored")
        if conn_list is None:
            conn_list = []
        self._conn_list = conn_list

    def generate_synapse_list(
            self, presynaptic_population, postsynaptic_population, delay_scale,
            weight_scale, synapse_type):

        prevertex = presynaptic_population._get_vertex
        postvertex = postsynaptic_population._get_vertex

        # Convert connection list into numpy record array
        conn_list_numpy = numpy.array(
            self._conn_list, dtype=[("source", "uint32"), ("target", "uint32"),
                                    ("weight", "float"), ("delay", "float")])
        if (conn_list_numpy["target"] >= postvertex.n_atoms).any():
            raise exceptions.ConfigurationException("Target atom out of range")

        # Sort by pre-synaptic neuron
        conn_list_numpy = numpy.sort(conn_list_numpy, order="source")

        # Apply weight and delay scaling
        conn_list_numpy["weight"] *= weight_scale
        conn_list_numpy["delay"] *= delay_scale

        # Count number of connections per pre-synaptic neuron
        pre_counts = numpy.histogram(
            conn_list_numpy["source"], numpy.arange(prevertex.n_atoms + 1))[0]

        # Take cumulative sum of these counts to get start and end indices of
        # the blocks of connections coming from each pre-synaptic neuron
        pre_end_idxs = numpy.cumsum(pre_counts)
        pre_start_idxs = numpy.append(0, pre_end_idxs[:-1])

        # Loop through slices of connections
        synaptic_rows = []
        for _, (start, end) in enumerate(zip(pre_start_idxs, pre_end_idxs)):

            # Get slice
            pre_conns = conn_list_numpy[start:end]

            # Repeat synapse type correct number of times
            synapse_type_row = numpy.empty(len(pre_conns), dtype="uint32")
            synapse_type_row.fill(synapse_type)

            # Combine post-synaptic neuron ids, weights, delays
            # and synapse types together into synaptic row
            synaptic_rows.append(
                SynapseRowInfo(pre_conns["target"],
                               pre_conns["weight"],
                               pre_conns["delay"],
                               synapse_type_row))

        # Return full synaptic list
        return SynapticList(synaptic_rows)
