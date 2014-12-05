from spynnaker.pyNN.models.neural_projections.connectors.seed_info \
    import SeedInfo
from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_properties.synapse_row_info \
    import SynapseRowInfo
from spynnaker.pyNN.models.neural_properties.randomDistributions \
    import generate_parameter
from spynnaker.pyNN.exceptions import ConfigurationException
import logging

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
        self._delay_so_far = 0
        self._weight_seeds = SeedInfo()
        self._delay_seeds = SeedInfo()

    def generate_synapse_list(
            self, presynaptic_population, postsynaptic_population, delay_scale,
            weight_scale, synapse_type):

        prevertex = presynaptic_population._get_vertex
        postvertex = postsynaptic_population._get_vertex

        id_lists = list()
        weight_lists = list()
        delay_lists = list()
        type_lists = list()

        for _ in range(0, prevertex.n_atoms):
            id_lists.append(list())
            weight_lists.append(list())
            delay_lists.append(list())
            type_lists.append(list())

        for i in range(0, len(self._conn_list)):
            conn = self._conn_list[i]
            len_list = []
            if isinstance(conn[0], list):
                len_list.append(len(conn[0]))
            else:
                len_list.append(1)
            if isinstance(conn[1], list):
                len_list.append(len(conn[1]))
            else:
                len_list.append(1)
            if isinstance(conn[2], list) and (isinstance(conn[0], list)
                                              or isinstance(conn[1], list)):
                len_list.append(len(conn[2]))
            else:
                len_list.append(1)
            if isinstance(conn[3], list) and (isinstance(conn[0], list)
                                              or isinstance(conn[1], list)):
                len_list.append(len(conn[3]))
            else:
                len_list.append(1)
            valid_len = reduce(lambda x, y: x if (y == 1 or y == x) else
                               (y if x == 1 else 0), len_list, 1)
            if (valid_len):
                for j in range(valid_len):
                    pre_atom = generate_parameter(conn[0], j)
                    post_atom = generate_parameter(conn[1], j)
                    if not 0 <= pre_atom < prevertex.n_atoms:
                        raise ConfigurationException(
                            "Invalid neuron id in presynaptic population {}"
                            .format(pre_atom))
                    if not 0 <= post_atom < postvertex.n_atoms:
                        raise ConfigurationException(
                            "Invalid neuron id in postsynaptic population {}"
                            .format(post_atom))
                    weight = generate_parameter(conn[2], j) * weight_scale
                    delay = generate_parameter(conn[3], j) * delay_scale
                    id_lists[pre_atom].append(post_atom)
                    weight_lists[pre_atom].append(weight)
                    delay_lists[pre_atom].append(delay)
                    type_lists[pre_atom].append(synapse_type)

        connection_list = [SynapseRowInfo(id_lists[i], weight_lists[i],
                           delay_lists[i], type_lists[i])
                           for i in range(0, prevertex.n_atoms)]

        return SynapticList(connection_list)
