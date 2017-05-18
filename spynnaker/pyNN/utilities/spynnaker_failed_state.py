from spinn_front_end_common.utilities import exceptions
from spinn_front_end_common.utilities.failed_state import FailedState
from spynnaker.pyNN.spynnaker_simulator_interface \
    import SpynnakerSimulatorInterface


class SpynnakerFailedState(SpynnakerSimulatorInterface, FailedState):

    __slots__ = ()

    @property
    def graph_mapper(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    @property
    def has_reset_last(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    @property
    def has_ran(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    @property
    def increment_none_labelled_vertex_count(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    @property
    def placements(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    @property
    def machine_time_step(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    @property
    def max_supported_delay(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    @property
    def min_supported_delay(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    @property
    def none_labelled_vertex_count(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    @property
    def transceiver(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    @property
    def use_virtual_board(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    @staticmethod
    def run(simtime, callbacks=None):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    @staticmethod
    def exit():
        raise exceptions.ConfigurationException(
            "You cannot call exit until you have called setup "
            "or after end/stop has been called.")

    @staticmethod
    def stop():
        raise exceptions.ConfigurationException(
            "You cannot call end/stop until you have called setup "
            "or after end/stop has been called.")

    @staticmethod
    def reset(annotations=None):
        raise exceptions.ConfigurationException(
            "You cannot call reset until you have called setup "
            "or after end/t has been called.")

    @staticmethod
    def run_until(time_point, callbacks=None):
        raise exceptions.ConfigurationException(
            "You cannot call run_until until you have called setup "
            "or after end/stop has been called.")

    @staticmethod
    def run_for(simtime, callbacks=None):
        raise exceptions.ConfigurationException(
            "You cannot call run_for until you have called setup "
            "or after end/stop has been called.")

    @staticmethod
    def get_current_time():
        raise exceptions.ConfigurationException(
            "You cannot call get_current_time until you have called setup "
            "or after end/stop has been called.")

    @staticmethod
    def get_time_step():
        raise exceptions.ConfigurationException(
            "You cannot call get_time_step until you have called setup "
            "or after end/stop has been called.")

    @staticmethod
    def get_min_delay():
        raise exceptions.ConfigurationException(
            "You cannot call get_min_delay until you have called setup "
            "or after end/stop has been called.")

    @staticmethod
    def get_max_delay():
        raise exceptions.ConfigurationException(
            "You cannot call get_max_delay until you have called setup "
            "or after end/stop has been called.")

    @staticmethod
    def num_processes():
        raise exceptions.ConfigurationException(
            "You cannot call num_processes until you have called setup "
            "or after end/stop has been called.")

    @staticmethod
    def rank():
        raise exceptions.ConfigurationException(
            "You cannot call rank until you have called setup "
            "or after end/stop has been called.")

    @staticmethod
    def initialize(cells, **initial_values):
        raise exceptions.ConfigurationException(
            "You cannot call initialize until you have called setup"
            "or after end/stop has been called.")

    @staticmethod
    def create(ellclass, cellparams=None, n=1):
        raise exceptions.ConfigurationException(
            "You cannot call create until you have called setup"
            "or after end/stop has been called.")

    @staticmethod
    def connect(
            pre, post, weight=0.0, delay=None, receptor_type=None, p=1,
            rng=None):
        raise exceptions.ConfigurationException(
            "You cannot call connect until you have called setup"
            "or after end/stop has been called.")

    @staticmethod
    def record(variables, source, filename, sampling_interval=None,
               annotations=None):
        raise exceptions.ConfigurationException(
            "You cannot call record until you have called setup"
            "or after end/stop has been called.")

    @staticmethod
    def min_delay():
        raise exceptions.ConfigurationException(
            "You cannot call min_delay until you have called setup"
            "or after end/stop has been called.")

    @staticmethod
    def _add_socket_address(self, x):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    def get_distribution_to_stats(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    def is_a_pynn_random(self, thing):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    def get_pynn_NumpyRNG(self):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")

    def set_number_of_neurons_per_core(self, neuron_type, max_permitted):
        raise exceptions.ConfigurationException(
            "This call is only valid between setup and end/stop")
