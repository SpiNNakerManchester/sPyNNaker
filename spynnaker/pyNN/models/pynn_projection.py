from spynnaker.pyNN.models.neuron.synapse_dynamics.synapse_dynamics_static \
    import SynapseDynamicsStatic
from spynnaker.pyNN.models.neuron.abstract_population_vertex \
    import AbstractPopulationVertex
from spynnaker.pyNN.models.pynn_projection_common import PyNNProjectionCommon

from spinn_front_end_common.utilities import exceptions

import logging

logger = logging.getLogger(__name__)


# noinspection PyProtectedMember
class Projection(PyNNProjectionCommon):
    """ A container for all the connections of a given type (same synapse type\
        and plasticity mechanisms) between two populations, together with\
        methods to set parameters of those connections, including of\
        plasticity mechanisms.
    """

    # noinspection PyUnusedLocal
    def __init__(
            self, presynaptic_population, postsynaptic_population, label,
            connector, spinnaker_control, machine_time_step, user_max_delay,
            timescale_factor, source=None, target='excitatory',
            synapse_dynamics=None, rng=None):

        synapse_dynamics_stdp = None
        if synapse_dynamics is None:
            synapse_dynamics_stdp = SynapseDynamicsStatic()
        else:
            synapse_dynamics_stdp = synapse_dynamics.slow
        postsynaptic_population._get_vertex.synapse_dynamics = \
            synapse_dynamics_stdp

        synapse_type = postsynaptic_population._get_vertex \
            .synapse_type.get_synapse_id_by_target(target)
        if synapse_type is None:
            raise exceptions.ConfigurationException(
                "Synapse target {} not found in {}".format(
                    target, postsynaptic_population.label))

        PyNNProjectionCommon.__init__(
            self, spinnaker_control=spinnaker_control, connector=connector,
            synapse_dynamics_stdp=synapse_dynamics_stdp,
            synapse_type=synapse_type,
            pre_synaptic_population=presynaptic_population,
            post_synaptic_population=postsynaptic_population,
            rng=rng, machine_time_step=machine_time_step,
            user_max_delay=user_max_delay, label=label,
            time_scale_factor=spinnaker_control.time_scale_factor)

        if not isinstance(postsynaptic_population._get_vertex,
                          AbstractPopulationVertex):

            raise exceptions.ConfigurationException(
                "postsynaptic population is not designed to receive"
                " synaptic projections")

    def describe(self, template='projection_default.txt', engine='default'):
        """ Return a human-readable description of the projection.

        The output may be customised by specifying a different template
        together with an associated template engine (see ``pyNN.descriptions``)

        If template is None, then a dictionary containing the template context
        will be returned.
        """
        # TODO
        raise NotImplementedError

    def __getitem__(self, i):
        """Return the `i`th connection within the Projection."""
        # TODO: Need to work out what is being returned
        raise NotImplementedError

    # noinspection PyPep8Naming
    def getSynapseDynamics(self, parameter_name, list_format='list',
                           gather=True):
        """ Get parameters of the dynamic synapses for all connections in this\
            Projection.
        :param parameter_name:
        :param list_format:
        :param gather:
        """
        # TODO: Need to work out what is to be returned
        raise NotImplementedError

    # noinspection PyPep8Naming
    def getWeights(self, format='list', gather=True):  # @ReservedAssignment
        """
        Get synaptic weights for all connections in this Projection.

        Possible formats are: a list of length equal to the number of
        connections in the projection, a 2D weight array (with NaN for
        non-existent connections). Note that for the array format, if there is
        more than connection between two cells, the summed weight will be
        given.
        :param format: the type of format to be returned (only support "list")
        :param gather: gather the weights from stuff. currently has no meaning\
                in spinnaker when set to false. Therefore is always true
        """
        if not gather:
            exceptions.ConfigurationException(
                "the gather param has no meaning for spinnaker when set to "
                "false")

        return self._get_synaptic_data(format == 'list', "weight")

    # noinspection PyPep8Naming
    def getDelays(self, format='list', gather=True):  # @ReservedAssignment
        """
        Get synaptic delays for all connections in this Projection.

        Possible formats are: a list of length equal to the number of
        connections in the projection, a 2D delay array (with NaN for
        non-existent connections).
        """
        if not gather:
            exceptions.ConfigurationException(
                "the gather param has no meaning for spinnaker when set to "
                "false")

        return self._get_synaptic_data(format == 'list', "delay")

    def __len__(self):
        """ Return the total number of local connections.
        """

        # TODO: Need to work out what this means
        raise NotImplementedError

    # noinspection PyPep8Naming
    def printDelays(self, file_name, list_format='list', gather=True):
        """ Print synaptic weights to file. In the array format, zeros are\
            printed for non-existent connections.
        """
        # TODO:
        raise NotImplementedError

    # noinspection PyPep8Naming
    def printWeights(self, file_name, list_format='list', gather=True):
        """ Print synaptic weights to file. In the array format, zeros are\
            printed for non-existent connections.
        """
        # TODO:
        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomizeWeights(self, rand_distr):
        """ Set weights to random values taken from rand_distr.
        """
        # TODO: Requires that the synapse list is not created proactively
        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomizeDelays(self, rand_distr):
        """ Set delays to random values taken from rand_distr.
        """
        # TODO: Requires that the synapse list is not created proactively
        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomizeSynapseDynamics(self, param, rand_distr):
        """ Set parameters of the synapse dynamics to values taken from\
            rand_distr
        """
        # TODO: Look at what this is randomising
        raise NotImplementedError

    def __repr__(self):
        return "projection {}".format(self._projection_edge.label)

    # noinspection PyPep8Naming
    def saveConnections(self, file_name, gather=True, compatible_output=True):
        """ Save connections to file in a format suitable for reading in with\
            a FromFileConnector.
        """
        # TODO
        raise NotImplementedError

    def size(self, gather=True):
        """ Return the total number of connections.
         - only local connections, if gather is False,
         - all connections, if gather is True (default)
        """
        # TODO
        raise NotImplementedError

    # noinspection PyPep8Naming
    def setDelays(self, d):
        """ Set the delays

        d can be a single number, in which case all delays are set to this\
        value, or a list/1D array of length equal to the number of connections\
        in the projection, or a 2D array with the same dimensions as the\
        connectivity matrix (as returned by `getDelays(format='array')`).
        """
        # TODO: Requires that the synapse list is not created proactively
        raise NotImplementedError

    # noinspection PyPep8Naming
    def setSynapseDynamics(self, param, value):
        """ Set parameters of the dynamic synapses for all connections in this\
            projection.
        """
        # TODO: Need to set this in the edge
        raise NotImplementedError

    # noinspection PyPep8Naming
    def setWeights(self, w):
        """ Set the weights

        w can be a single number, in which case all weights are set to this\
        value, or a list/1D array of length equal to the number of connections\
        in the projection, or a 2D array with the same dimensions as the\
        connectivity matrix (as returned by `getWeights(format='array')`).\
        Weights should be in nA for current-based and uS for conductance-based\
        synapses.
        """

        # TODO: Requires that the synapse list is not created proactively
        raise NotImplementedError

    # noinspection PyPep8Naming
    def weightHistogram(self, min_weight=None, max_weight=None, nbins=10):
        """ Return a histogram of synaptic weights.

        If min and max are not given, the minimum and maximum weights are\
        calculated automatically.
        """
        # TODO
        raise NotImplementedError
