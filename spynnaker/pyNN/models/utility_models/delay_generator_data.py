import numpy
import decimal
from data_specification.enums.data_type import DataType


class DelayGeneratorData(object):
    """ Data for each connection of the delay generator
    """

    BASE_SIZE = 8 * 4

    def __init__(
            self, max_row_n_synapses, max_delayed_row_n_synapses,
            pre_slices, pre_slice_index, post_slices, post_slice_index,
            pre_vertex_slice, post_vertex_slice, synapse_information,
            max_stage, machine_time_step):
        self._max_row_n_synapses = max_row_n_synapses
        self._max_delayed_row_n_synapses = max_delayed_row_n_synapses
        self._pre_slices = pre_slices
        self._pre_slice_index = pre_slice_index
        self._post_slices = post_slices
        self._post_slice_index = post_slice_index
        self._pre_vertex_slice = pre_vertex_slice
        self._post_vertex_slice = post_vertex_slice
        self._synapse_information = synapse_information
        self._max_stage = max_stage
        self._machine_time_step = machine_time_step

    @property
    def size(self):
        """ The size of the generated data in bytes

        :rtype: int
        """
        connector = self._synapse_information.connector

        return sum((self.BASE_SIZE,
                    connector.gen_connector_params_size_in_bytes,
                    connector.gen_delay_params_size_in_bytes))

    @property
    def gen_data(self):
        """ Get the data to be written for this connection

        :rtype: numpy array of uint32
        """
        connector = self._synapse_information.connector
        items = list()
        items.append(numpy.array([
            self._max_row_n_synapses,
            self._max_delayed_row_n_synapses,
            self._post_vertex_slice.lo_atom,
            self._post_vertex_slice.n_atoms,
            self._max_stage,
            (decimal.Decimal(str(1000.0 / float(self._machine_time_step))) *
             DataType.S1615.scale),
            connector.gen_connector_id,
            connector.gen_delays_id],
            dtype="uint32"))
        items.append(connector.gen_connector_params(
            self._pre_slices, self._pre_slice_index, self._post_slices,
            self._post_slice_index, self._pre_vertex_slice,
            self._post_vertex_slice, self._synapse_information.synapse_type))
        items.append(connector.gen_delay_params(
            self._pre_vertex_slice, self._post_vertex_slice))
        return numpy.concatenate(items)
