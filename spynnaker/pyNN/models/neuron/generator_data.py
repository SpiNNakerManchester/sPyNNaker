from enum import IntEnum, auto


class _ConnectorType(IntEnum):
    ONE_TO_ONE = auto()
    FIXED_PROBABILITY = auto()


class _MatrixType(IntEnum):
    STATIC = auto()
    STDP = auto()



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
        self._pre_slice_start = pre_vertex_slice.lo_atom
        self._pre_slice_count = pre_vertex_slice.n_atoms
        self._delay_chip = (delay_placement.y << 8) | delay_placement.x
        self._delay_core = delay_placement.p
        self._synapse_type = synapse_information.synapse_type

        connector = synapse_information.connector
        synapse_dynamics = synapse_information.synapse_dynamics
        self._connector_type_hash = connector.gen_connector_id
        self._matrix_type_hash = synapse_dynamics.gen_matrix_id
        self._weight_type_hash = connector.gen_weights_id
        self._delay_type_hash = connector.gen_delays_id
