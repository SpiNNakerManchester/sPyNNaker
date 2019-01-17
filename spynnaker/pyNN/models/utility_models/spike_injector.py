from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from .spike_injector_vertex import SpikeInjectorVertex

_population_parameters = {
    "port": None,
    "virtual_key": None,
    "spike_buffer_max_size": None,
    "buffer_size_before_receive": None,
    "time_between_requests": None,
    "buffer_notification_ip_address": None,
    "buffer_notification_port": None
}


class SpikeInjector(AbstractPyNNModel):

    default_population_parameters = _population_parameters

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=_population_parameters.keys())
    def create_vertex(
            self, n_neurons, label, constraints, port, virtual_key,
            spike_buffer_max_size, buffer_size_before_receive,
            time_between_requests, buffer_notification_ip_address,
            buffer_notification_port):
        return SpikeInjectorVertex(
            n_neurons, label, constraints, port, virtual_key,
            spike_buffer_max_size, buffer_size_before_receive,
            time_between_requests, buffer_notification_ip_address,
            buffer_notification_port)
