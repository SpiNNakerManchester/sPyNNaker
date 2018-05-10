import numpy


class GeneratorData(object):
    """ Data for each connection of the synapse generator
    """

    def __init__(
            self, synaptic_matrix_offset, delayed_synaptic_matrix_offset,
            max_row_length, max_delayed_row_length, pre_vertex_slice,
            delay_placement, synapse_information):
        self._synaptic_matrix_offset = synaptic_matrix_offset
        self._delayed_synaptic_matrix_offset = delayed_synaptic_matrix_offset
        self._max_row_length = max_row_length
        self._max_delayed_row_length = max_delayed_row_length
        self._pre_vertex_slice = pre_vertex_slice
        self._delay_placement = delay_placement
        self._synapse_information = synapse_information

    @property
    def gen_data(self):
        """ Get the data to be written for this connection

        :rtype: numpy array of uint32
        """
        connector = self._synapse_information.connector
        synapse_dynamics = self._synapse_information.synapse_dynamics
        items = list()
        items.append(numpy.array([
            self._synaptic_matrix_offset,
            self._delayed_synaptic_matrix_offset,
            self._max_row_length,
            self._max_delayed_row_length,
            self._pre_vertex_slice.lo_atom,
            self._pre_vertex_slice.n_atoms,
            (self._delay_placement.y << 8) | self._delay_placement.x,
            self._delay_placement.p,
            self._synapse_information.synapse_type,
            synapse_dynamics.gen_matrix_id,
            connector.gen_connector_id,
            connector.gen_weights_id,
            connector.get_delays_id],
            dtype="uint32"))
        items.append(synapse_dynamics.gen_matrix_params)
        items.append(connector.gen_connector_params)
        items.append(connector.gen_weights_params)
        items.append(connector.gen_delay_params)
        return numpy.concatenate(items)
