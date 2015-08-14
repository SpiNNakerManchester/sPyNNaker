from spynnaker.pyNN.connectors.abstract_connector import AbstractConnector
from spynnaker.pyNN.models.neuron.synaptic_list import SynapticList
from spynnaker.pyNN.models.neuron.synapse_row_info import SynapseRowInfo
from spynnaker.pyNN.models.neural_properties.randomDistributions \
    import generate_parameter_array
import numpy


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

        source_ids = numpy.random.choice(
            prevertex.n_atoms, size=self._num_synapses, replace=True)
        source_ids.sort()
        target_ids = numpy.random.choice(
            postvertex.n_atoms, size=self._num_synapses, replace=True)
        weights = generate_parameter_array(
            self._weights, self._num_synapses, target_ids) * weight_scale
        delays = generate_parameter_array(
            self._delays, self._num_synapses, target_ids) * delay_scale

        pre_counts = numpy.histogram(source_ids,
                                     numpy.arange(prevertex.n_atoms + 1))[0]
        pre_end_idxs = numpy.cumsum(pre_counts)
        pre_start_idxs = numpy.append(0, pre_end_idxs[:-1])

        synaptic_rows = []
        n_synapses = 0
        for _, (start, end) in enumerate(zip(pre_start_idxs, pre_end_idxs)):

            this_target_ids = target_ids[start:end]
            this_weights = weights[start:end]
            this_delays = delays[start:end]
            this_synapes_types = numpy.ones(
                len(this_target_ids), dtype="uint32") * synapse_type
            n_synapses += len(this_target_ids)

            synaptic_rows.append(SynapseRowInfo(
                this_target_ids, this_weights, this_delays,
                this_synapes_types))

        return SynapticList(synaptic_rows)
