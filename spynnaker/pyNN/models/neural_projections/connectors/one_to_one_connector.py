from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_properties.synapse_row_info \
    import SynapseRowInfo
from spynnaker.pyNN.models.neural_properties.randomDistributions \
    import generate_parameter
from spynnaker.pyNN.exceptions import ConfigurationException


class OneToOneConnector(AbstractConnector):
    """
    Where the pre- and postsynaptic populations have the same size, connect
    cell i in the presynaptic pynn_population.py to cell i in the postsynaptic
    pynn_population.py for all i.

    :param weights:
        may either be a float, a !RandomDistribution object, a list/
        1D array with at least as many items as connections to be
        created. Units nA.
    :param delays:
        as `weights`. If `None`, all synaptic delays will be set
        to the global minimum delay.

    """
    def __init__(self, weights=0.0, delays=1):
        """
        Creates a new connector.
        """
        self._weights = weights
        self._delays = delays

    def generate_synapse_list(
            self, presynaptic_population, postsynaptic_population, delay_scale,
            weight_scale, synapse_type):

        prevertex = presynaptic_population._get_vertex
        postvertex = postsynaptic_population._get_vertex

        if prevertex.n_atoms != postvertex.n_atoms:
            raise ConfigurationException("The two populations to be connected "
                                         "with a One to One connector have to "
                                         "have the same size")
        connection_list = list()
        for pre_atom in range(0, prevertex.n_atoms):
            delay = generate_parameter(self._delays, pre_atom) * delay_scale
            weight = generate_parameter(self._weights, pre_atom) * weight_scale
            connection_list.append(SynapseRowInfo([pre_atom], [weight],
                                   [delay], [synapse_type]))

        return SynapticList(connection_list)
