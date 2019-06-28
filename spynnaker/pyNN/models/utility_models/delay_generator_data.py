import decimal
import numpy
from data_specification.enums.data_type import DataType


class DelayGeneratorData(object):
    """ Data for each connection of the delay generator
    """
    __slots__ = (
        "__machine_time_step",
        "__max_delayed_row_n_synapses",
        "__max_row_n_synapses",
        "__max_stage",
        "__post_slices",
        "__post_slice_index",
        "__post_vertex_slice",
        "__pre_slices",
        "__pre_slice_index",
        "__pre_vertex_slice",
        "__synapse_information")

    BASE_SIZE = 8 * 4

    def __init__(
            self, max_row_n_synapses, max_delayed_row_n_synapses,
            pre_slices, pre_slice_index, post_slices, post_slice_index,
            pre_vertex_slice, post_vertex_slice, synapse_information,
            max_stage, machine_time_step):
        self.__max_row_n_synapses = max_row_n_synapses
        self.__max_delayed_row_n_synapses = max_delayed_row_n_synapses
        self.__pre_slices = pre_slices
        self.__pre_slice_index = pre_slice_index
        self.__post_slices = post_slices
        self.__post_slice_index = post_slice_index
        self.__pre_vertex_slice = pre_vertex_slice
        self.__post_vertex_slice = post_vertex_slice
        self.__synapse_information = synapse_information
        self.__max_stage = max_stage
        self.__machine_time_step = machine_time_step

    @property
    def size(self):
        """ The size of the generated data in bytes

        :rtype: int
        """
        connector = self.__synapse_information.connector

        return sum((self.BASE_SIZE,
                    connector.gen_connector_params_size_in_bytes,
                    connector.gen_delay_params_size_in_bytes(
                        self.__synapse_information.delay)))

    @property
    def gen_data(self):
        """ Get the data to be written for this connection

        :rtype: numpy array of uint32
        """
        connector = self.__synapse_information.connector
        items = list()
        items.append(numpy.array([
            self.__max_row_n_synapses,
            self.__max_delayed_row_n_synapses,
            self.__post_vertex_slice.lo_atom,
            self.__post_vertex_slice.n_atoms,
            self.__max_stage,
            (decimal.Decimal(str(1000.0 / float(self.__machine_time_step))) *
             DataType.S1615.scale),
            connector.gen_connector_id,
            connector.gen_delays_id(self.__synapse_information.delay)],
            dtype="uint32"))
        items.append(connector.gen_connector_params(
            self.__pre_slices, self.__pre_slice_index, self.__post_slices,
            self.__post_slice_index, self.__pre_vertex_slice,
            self.__post_vertex_slice, self.__synapse_information.synapse_type))
        items.append(connector.gen_delay_params(
            self.__synapse_information.delay, self.__pre_vertex_slice,
            self.__post_vertex_slice))
        return numpy.concatenate(items)
