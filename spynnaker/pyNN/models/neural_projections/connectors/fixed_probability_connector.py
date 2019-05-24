import decimal
import math
import numpy
from spinn_utilities.overrides import overrides
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.utilities import utility_calls
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)


class FixedProbabilityConnector(AbstractGenerateConnectorOnMachine):
    """ For each pair of pre-post cells, the connection probability is constant.
    """

    __slots__ = [
        "__allow_self_connections",
        "_p_connect"]

    def __init__(
            self, p_connect, allow_self_connections=True, safe=True,
            verbose=False, rng=None):
        """
        :param p_connect:
            a float between zero and one. Each potential connection is created\
            with this probability.
        :type p_connect: float
        :param allow_self_connections:
            if the connector is used to connect a Population to itself, this\
            flag determines whether a neuron is allowed to connect to itself,\
            or only to other neurons in the Population.
        :type allow_self_connections: bool
        :param `pyNN.Space` space:
            a Space object, needed if you wish to specify distance-dependent\
            weights or delays - not implemented
        """
        super(FixedProbabilityConnector, self).__init__(safe, verbose)
        self._p_connect = p_connect
        self.__allow_self_connections = allow_self_connections
        self._rng = rng
        if not 0 <= self._p_connect <= 1:
            raise ConfigurationException(
                "The probability must be between 0 and 1 (inclusive)")

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, delays):
        n_connections = utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_post_neurons,
            self._n_pre_neurons * self._n_post_neurons, self._p_connect)
        return self._get_delay_maximum(delays, n_connections)

    def _get_n_connections(self, out_of):
        return utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_post_neurons, out_of,
            self._p_connect)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, delays, post_vertex_slice, min_delay=None, max_delay=None):
        # pylint: disable=too-many-arguments
        n_connections = utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_post_neurons,
            post_vertex_slice.n_atoms, self._p_connect)

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            delays, self._n_pre_neurons * self._n_post_neurons,
            n_connections, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        # pylint: disable=too-many-arguments
        n_connections = utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_post_neurons,
            self._n_pre_neurons, self._p_connect)
        return n_connections

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, weights):
        # pylint: disable=too-many-arguments
        n_connections = utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_post_neurons,
            self._n_pre_neurons * self._n_post_neurons, self._p_connect)
        return self._get_weight_maximum(weights, n_connections)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, weights, delays, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        # pylint: disable=too-many-arguments
        n_items = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        items = self._rng.next(n_items)

        # If self connections are not allowed, remove possibility the self
        # connections by setting them to a value of infinity
        if not self.__allow_self_connections:
            items[0:n_items:post_vertex_slice.n_atoms + 1] = numpy.inf

        present = items < self._p_connect
        ids = numpy.where(present)[0]
        n_connections = numpy.sum(present)

        block = numpy.zeros(n_connections, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = (
            (ids // post_vertex_slice.n_atoms) + pre_vertex_slice.lo_atom)
        block["target"] = (
            (ids % post_vertex_slice.n_atoms) + post_vertex_slice.lo_atom)
        block["weight"] = self._generate_weights(
            weights, n_connections, None)
        block["delay"] = self._generate_delays(
            delays, n_connections, None)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "FixedProbabilityConnector({})".format(self._p_connect)

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self):
        return ConnectorIDs.FIXED_PROBABILITY_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params)
    def gen_connector_params(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        params = [
            self.__allow_self_connections,
            round(decimal.Decimal(
                str(self._p_connect)) * DataType.U032.scale)]
        params.extend(self._get_connector_seed(
            pre_vertex_slice, post_vertex_slice, self._rng))
        return numpy.array(params, dtype="uint32")

    @property
    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        return 8 + 16
