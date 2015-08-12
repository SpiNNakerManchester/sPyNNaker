from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_properties.synapse_row_info \
    import SynapseRowInfo
from spynnaker.pyNN.models.neural_properties.randomDistributions \
    import generate_parameter_array
from spinn_front_end_common.utilities import exceptions
import numpy


class FixedProbabilityConnector(AbstractConnector):
    """
    For each pair of pre-post cells, the connection probability is constant.

    :param `float` p_connect:
        a float between zero and one. Each potential connection
        is created with this probability.
    :param `bool` allow_self_connections:
        if the connector is used to connect a
        Population to itself, this flag determines whether a neuron is
        allowed to connect to itself, or only to other neurons in the
        Population.
    :param weights:
        may either be a float, a !RandomDistribution object, a list/
        1D array with at least as many items as connections to be
        created. Units nA.
    :param delays:
        If `None`, all synaptic delays will be set
        to the global minimum delay.
    :param `pyNN.Space` space:
        a Space object, needed if you wish to specify distance-
        dependent weights or delays - not implemented
    """
    def __init__(self, p_connect, weights=0.0, delays=1,
                 allow_self_connections=True):
        """
        Creates a new FixedProbabilityConnector.
        """
        self._p_connect = p_connect
        self._weights = weights
        self._delays = delays
        self._allow_self_connections = allow_self_connections

        if not 0 <= self._p_connect <= 1:
            raise exceptions.ConfigurationException(
                "The probability should be between 0 and 1 (inclusive)")

    def generate_synapse_list(
            self, presynaptic_population, postsynaptic_population, delay_scale,
            weight_scale, synapse_type):

        prevertex = presynaptic_population._get_vertex
        postvertex = postsynaptic_population._get_vertex

        present = (numpy.random.rand(postvertex.n_atoms * prevertex.n_atoms) <=
                   self._p_connect)
        ids = numpy.where(present)[0]
        n_present = numpy.sum(present)

        source_ids = ids / postvertex.n_atoms
        source_ids.sort()
        target_ids = ids % postvertex.n_atoms
        delays = generate_parameter_array(
            self._delays, n_present, present) * delay_scale
        weights = generate_parameter_array(
            self._weights, n_present, present) * weight_scale

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
