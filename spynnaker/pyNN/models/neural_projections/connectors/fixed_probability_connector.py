from spinn_utilities.overrides import overrides
from spynnaker.pyNN.utilities import utility_calls
from .abstract_connector import AbstractConnector
import decimal
from .abstract_generate_connector_on_machine \
    import AbstractGenerateConnectorOnMachine, ConnectorIDs
from spinn_front_end_common.utilities.exceptions import ConfigurationException
import math
import numpy
from data_specification.enums.data_type import DataType


class FixedProbabilityConnector(AbstractGenerateConnectorOnMachine):
    __slots__ = [
        "_allow_self_connections",
        "_p_connect"]

    """
    For each pair of pre-post cells, the connection probability is constant.

    :param p_connect:
        a float between zero and one. Each potential connection is created\
        with this probability.
    :type p_connect: float
    :param allow_self_connections:
        if the connector is used to connect a Population to itself, this flag\
        determines whether a neuron is allowed to connect to itself, or only\
        to other neurons in the Population.
    :type allow_self_connections: bool
    :param `pyNN.Space` space:
        a Space object, needed if you wish to specify distance-dependent\
        weights or delays - not implemented
    """
    def __init__(
            self, p_connect, allow_self_connections=True, safe=True,
            verbose=False):
        super(FixedProbabilityConnector, self).__init__(safe, verbose)
        self._p_connect = p_connect
        self._allow_self_connections = allow_self_connections

        if not 0 <= self._p_connect <= 1:
            raise ConfigurationException(
                "The probability must be between 0 and 1 (inclusive)")

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays, utility_calls.get_probable_maximum_selected(
                self._n_pre_neurons * self._n_post_neurons,
                self._n_pre_neurons * self._n_post_neurons, self._p_connect))

    @overrides(AbstractConnector.get_delay_variance)
    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        return self._get_delay_variance(self._delays, None)

    def _get_n_connections(self, out_of):
        return utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_post_neurons, out_of,
            self._p_connect)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        # pylint: disable=too-many-arguments
        n_connections = self._get_n_connections(post_vertex_slice.n_atoms)

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._delays, self._n_pre_neurons * self._n_post_neurons,
            n_connections, None, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        return self._get_n_connections(pre_vertex_slice.n_atoms)

    @overrides(AbstractConnector.get_weight_mean)
    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        return self._get_weight_mean(self._weights, None)

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        n_connections = self._get_n_connections(
            pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms)
        return self._get_weight_maximum(
            self._weights, n_connections, None)

    @overrides(AbstractConnector.get_weight_variance)
    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        return self._get_weight_variance(self._weights, None)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        # pylint: disable=too-many-arguments
        n_items = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        items = self._rng.next(n_items)

        # If self connections are not allowed, remove possibility the self
        # connections by setting them to a value of infinity
        if not self._allow_self_connections:
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
            self._weights, n_connections, None)
        block["delay"] = self._generate_delays(
            self._delays, n_connections, None)
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
            self.allow_self_connections,
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
