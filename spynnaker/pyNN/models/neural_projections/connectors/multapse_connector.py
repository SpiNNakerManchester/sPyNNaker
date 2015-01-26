from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_properties.synapse_row_info \
    import SynapseRowInfo
from spynnaker.pyNN.models.neural_properties.randomDistributions \
    import generate_parameter
import random


class MultapseConnector(AbstractConnector):
    """
    Create a multapse connector. The size of the source and destination
    populations are obtained when the projection is connected. The number of
    synapses is specified. when instantiated, the required number of synapses
    is created by selecting at random from the source and target populations
    with replacement. Uniform selection probability is assumed.

    : param numSynapses:
        Integer. This is the total number of synapses in the connection.
    :param weights:
        may either be a float, a !RandomDistribution object, a list/
        1D array with at least as many items as connections to be
        created. Units nA.
    :param delays:
        as `weights`. If `None`, all synaptic delays will be set
        to the global minimum delay.

    """
    def __init__(self, num_synapses=0, weights=0.0, delays=1,
                 connection_array=None):
        """
        Creates a new connector.
        """
        self._num_synapses = num_synapses
        self._weights = weights
        self._delays = delays
        self._connection_array = connection_array

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

        num_incoming_axons = prevertex.n_atoms
        num_target_neurons = postvertex.n_atoms

        for _ in range(0, self._num_synapses):
            source = int(random.random() * num_incoming_axons)
            target = int(random.random() * num_target_neurons)
            weight = generate_parameter(self._weights, target) * weight_scale
            delay = generate_parameter(self._delays, target) * delay_scale
            id_lists[source].append(target)
            weight_lists[source].append(weight)
            delay_lists[source].append(delay)
            type_lists[source].append(synapse_type)

        connection_list = [SynapseRowInfo(id_lists[i], weight_lists[i],
                           delay_lists[i], type_lists[i])
                           for i in range(0, prevertex.n_atoms)]

        return SynapticList(connection_list)
