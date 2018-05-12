import numpy


class GeneratorData(object):
    """ Data for each connection of the synapse generator
    """

    BASE_SIZE = 14 * 4

    def __init__(
            self, synaptic_matrix_offset, delayed_synaptic_matrix_offset,
            max_row_length, max_delayed_row_length, pre_vertex_slice,
            delay_placement, synapse_information, max_stage):
        self._synaptic_matrix_offset = synaptic_matrix_offset
        self._delayed_synaptic_matrix_offset = delayed_synaptic_matrix_offset
        self._max_row_length = max_row_length
        self._max_delayed_row_length = max_delayed_row_length
        self._pre_vertex_slice = pre_vertex_slice
        self._delay_placement = delay_placement
        self._synapse_information = synapse_information
        self._max_stage = max_stage

    @property
    def size(self):
        """ The size of the generated data in bytes

        :rtype: int
        """
        connector = self._synapse_information.connector
        dynamics = self._synapse_information.synapse_dynamics

        return sum((self.BASE_SIZE,
                    dynamics.gen_matrix_params_size_in_bytes,
                    connector.gen_connector_params_size_in_bytes,
                    connector.gen_weight_params_size_in_bytes,
                    connector.gen_delay_params_size_in_bytes,
                    connector.gen_rng_params_size_in_bytes))

    @property
    def gen_data(self):
        """ Get the data to be written for this connection

        :rtype: numpy array of uint32
        """
        connector = self._synapse_information.connector
        synapse_dynamics = self._synapse_information.synapse_dynamics
        delay_chip = 0xFFFFFFFF
        delay_core = 0xFFFFFFFF
        if self._delay_placement is not None:
            delay_chip = (
                (self._delay_placement.y << 8) | self._delay_placement.x)
            delay_core = self._delay_placement.p
        items = list()
        items.append(numpy.array([
            self._synaptic_matrix_offset,
            self._delayed_synaptic_matrix_offset,
            self._max_row_length,
            self._max_delayed_row_length,
            self._pre_vertex_slice.lo_atom,
            self._pre_vertex_slice.n_atoms,
            delay_chip, delay_core, self._max_stage,
            self._synapse_information.synapse_type,
            synapse_dynamics.gen_matrix_id,
            connector.gen_connector_id,
            connector.gen_weights_id,
            connector.gen_delays_id],
            dtype="uint32"))
        items.append(synapse_dynamics.gen_matrix_params)
        items.append(connector.gen_connector_params)
        items.append(connector.gen_weights_params)
        items.append(connector.gen_delay_params)
        items.append(connector.gen_rng_params)
        return numpy.concatenate(items)
