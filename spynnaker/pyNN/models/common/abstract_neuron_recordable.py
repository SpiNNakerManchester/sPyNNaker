from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractNeuronRecordable(object):
    """ Indicates that membrane voltage can be recorded from this object
    """

    __slots__ = ()

    @abstractmethod
    def get_recordable_variables(self):
        """
        Returns a list of the variables this models is expected to collect
        """

    @abstractmethod
    def is_recording(self, variable):
        """ Determines if variable is being recorded

        :return: True if vavriable are being recorded, False otherwise
        :rtype: bool
        """

    @abstractmethod
    def set_recording(self, variable, new_state=True, sampling_interval=None,
                      indexes=None):
        """ Sets v to being recorded
        """

    @abstractmethod
    def clear_recording(self, variable, buffer_manager, placements,
                        graph_mapper):
        """ clears the recorded data from the object

        :param buffer_manager: the buffer manager object
        :param placements: the placements object
        :param graph_mapper: the graph mapper object
        :rtype: None
        """

    @abstractmethod
    def get_data(self, variable, n_machine_time_steps, placements,
                 graph_mapper, buffer_manager, machine_time_step):
        """

        :param variable:
        :param n_machine_time_steps:
        :param placements:
        :param graph_mapper:
        :param buffer_manager:
        :param machine_time_step:
        :return:
        """

    @abstractmethod
    def get_neuron_sampling_interval(self, variable):
        """
        Returns the current sampling interval for this variable
        :param variable: PyNN name of the variable
        :return: Sampling interval in micro seconds
        """
