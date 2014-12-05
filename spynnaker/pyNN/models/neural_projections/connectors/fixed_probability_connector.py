from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_properties.synapse_row_info \
    import SynapseRowInfo
from spynnaker.pyNN.models.neural_properties.randomDistributions \
    import generate_parameter_array
from spynnaker.pyNN.exceptions import ConfigurationException
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
            raise ConfigurationException("The probability should be between 0"
                                         " and 1 (inclusive)")

    def generate_synapse_list(
            self, presynaptic_population, postsynaptic_population, delay_scale,
            weight_scale, synapse_type):

        prevertex = presynaptic_population._get_vertex
        postvertex = postsynaptic_population._get_vertex

        rows = list()
        for pre_atom in range(0, prevertex.n_atoms):
            present = numpy.random.rand(postvertex.n_atoms) <= self._p_connect
            if (not self._allow_self_connections
                    and presynaptic_population == postsynaptic_population):
                present[pre_atom] = 0

            n_present = numpy.sum(present)

            ids = numpy.where(present)[0]

            delays = (generate_parameter_array(
                self._delays, n_present, present) * delay_scale)
            weights = (generate_parameter_array(
                self._weights, n_present, present) * weight_scale)
            synapse_types = (numpy.ones(len(ids), dtype='uint32')
                             * synapse_type)

            rows.append(SynapseRowInfo(ids, weights, delays, synapse_types))
        return SynapticList(rows)
