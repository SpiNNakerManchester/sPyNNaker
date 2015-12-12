from pyNN.random import RandomDistribution
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
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

    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays,
            self._n_pre_neurons * self._n_post_neurons * self._p_connect * 1.1)

    def get_n_connections_from_pre_vertex_maximum(
            self, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        if min_delay is None or max_delay is None:
            return post_vertex_slice.n_atoms * self._p_connect * 1.1
        else:
            n_connections = (
                pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms *
                self._p_connect * 1.1)
            connection_slice = self._connection_slice(
                pre_vertex_slice, post_vertex_slice)

            if isinstance(self._delays, RandomDistribution):
                return (utility_calls.get_probability_within_range(
                    self._delays, min_delay, max_delay) *
                    post_vertex_slice.n_atoms * self._p_connect * 1.1)
            elif not hasattr(self._delays, '__iter__'):
                if self._delays >= min_delay and self._delays <= max_delay:
                    return post_vertex_slice.n_atoms * self._p_connect * 1.1
                return 0
            else:
                max_length = max([len([delay for delay in self._delays[
                    self._connection_slice(slice(atom, atom + 1))]
                    if min_delay is None or max_delay is None or
                    (delay >= min_delay and delay <= max_delay)])
                    for atom in range(pre_vertex_slice.lo_atom,
                                      pre_vertex_slice.hi_atom + 1)])
                return max_length

            return self._get_n_connections_from_pre_vertex_with_delay_maximum(
                self._delays, n_connections, connection_slice,
                min_delay, max_delay)

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
