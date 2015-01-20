from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_properties.synapse_row_info \
    import SynapseRowInfo
from spynnaker.pyNN.models.neural_properties.randomDistributions \
    import generate_parameter_array
import numpy


class AllToAllConnector(AbstractConnector):
    """
    Connects all cells in the presynaptic pynn_population.py to all cells in
    the postsynaptic pynn_population.py.

    :param `bool` allow_self_connections:
        if the connector is used to connect a
        Population to itself, this flag determines whether a neuron is
        allowed to connect to itself, or only to other neurons in the
        Population.
    :param `float` weights:
        may either be a float, a !RandomDistribution object, a list/
        1D array with at least as many items as connections to be
        created. Units nA.
    :param `float` delays:  -- as `weights`. If `None`, all synaptic delays
        will be set to the global minimum delay.
    :param `pyNN.Space` space:
        a Space object, needed if you wish to specify distance-
        dependent weights or delays - not implemented

    """
    def __init__(self, weights=0.0, delays=1, allow_self_connections=True):
        """
        Creates a new AllToAllConnector.
        """
        self._weights = weights
        self._delays = delays
        self._allow_self_connections = allow_self_connections

    def generate_synapse_list(
            self, presynaptic_population, postsynaptic_population, delay_scale,
            weight_scale, synapse_type):

        prevertex = presynaptic_population._get_vertex
        postvertex = postsynaptic_population._get_vertex

        connection_list = list()
        for pre_atom in range(0, prevertex.n_atoms):
            present = numpy.ones(postvertex.n_atoms, dtype=numpy.uint32)
            if (not self._allow_self_connections
                    and presynaptic_population == postsynaptic_population):
                present[pre_atom] = 0
                n_present = postvertex.n_atoms - 1
            else:
                n_present = postvertex.n_atoms

            ids = numpy.where(present)[0]
            delays = (generate_parameter_array(
                self._delays, n_present, present) * delay_scale)
            weights = (generate_parameter_array(
                self._weights, n_present, present) * weight_scale)
            synapse_types = (numpy.ones(len(ids), dtype='uint32')
                             * synapse_type)

            connection_list.append(SynapseRowInfo(ids, weights, delays,
                                   synapse_types))

        return SynapticList(connection_list)
