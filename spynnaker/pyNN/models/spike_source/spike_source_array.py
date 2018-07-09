from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.utilities import constants
from .spike_source_array_vertex import SpikeSourceArrayVertex

_population_parameters = {
        'port': None, 'tag': None, 'ip_address': None, 'board_address': None,
        'max_on_chip_memory_usage_for_spikes_in_bytes': (
            constants.SPIKE_BUFFER_SIZE_BUFFERING_IN),
        'space_before_notification': 640,
        'spike_recorder_buffer_size': (
            constants.EIEIO_SPIKE_BUFFER_SIZE_BUFFERING_OUT),
        'buffer_size_before_receive': (
            constants.EIEIO_BUFFER_SIZE_BEFORE_RECEIVE)
    }


class SpikeSourceArray(AbstractPyNNModel):

    default_population_parameters = _population_parameters

    def __init__(self, spike_times=[]):
        self._spike_times = spike_times

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=_population_parameters.keys())
    def create_vertex(
            self, n_neurons, label, constraints, port, tag, ip_address,
            board_address, max_on_chip_memory_usage_for_spikes_in_bytes,
            space_before_notification, spike_recorder_buffer_size,
            buffer_size_before_receive):
        max_atoms = self.get_max_atoms_per_core()
        return SpikeSourceArrayVertex(
            n_neurons, self._spike_times, port, tag, ip_address, board_address,
            max_on_chip_memory_usage_for_spikes_in_bytes,
            space_before_notification, constraints, label,
            spike_recorder_buffer_size, buffer_size_before_receive, max_atoms)
