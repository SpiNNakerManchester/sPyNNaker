from spinn_front_end_common.utilities import exceptions
from spinn_front_end_common.utilities.failed_state import FailedState, \
    FAILED_STATE_MSG
from spynnaker.pyNN.spynnaker_simulator_interface \
    import SpynnakerSimulatorInterface


class SpynnakerFailedState(SpynnakerSimulatorInterface, FailedState, object):

    __slots__ = ()

    def get_distribution_to_stats(self):
        raise exceptions.ConfigurationException(FAILED_STATE_MSG)

    def get_current_time(self):
        raise exceptions.ConfigurationException(FAILED_STATE_MSG)

    def get_pynn_NumpyRNG(self):
        raise exceptions.ConfigurationException(FAILED_STATE_MSG)

    @property
    def has_reset_last(self):
        raise exceptions.ConfigurationException(FAILED_STATE_MSG)

    def is_a_pynn_random(self, thing):
        raise exceptions.ConfigurationException(FAILED_STATE_MSG)

    @property
    def max_delay(self):
        raise exceptions.ConfigurationException(FAILED_STATE_MSG)

    @property
    def min_delay(self):
        raise exceptions.ConfigurationException(FAILED_STATE_MSG)

    @staticmethod
    def reset(annotations=None):
        raise exceptions.ConfigurationException(FAILED_STATE_MSG)

    def set_number_of_neurons_per_core(self, neuron_type, max_permitted):
        raise exceptions.ConfigurationException(FAILED_STATE_MSG)
