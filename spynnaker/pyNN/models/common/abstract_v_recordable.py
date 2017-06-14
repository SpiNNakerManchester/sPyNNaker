from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractVRecordable(object):
    """ Indicates that membrane voltage can be recorded from this object
    """

    __slots__ = ()

    @abstractmethod
    def is_recording_v(self):
        """ Determines if v is being recorded

        :return: True if v are being recorded, False otherwise
        :rtype: bool
        """

    @abstractmethod
    def set_recording_v(self, new_state=True):
        """ Sets v to being recorded
        """

    @abstractmethod
    def clear_v_recording(self, buffer_manager, placements, graph_mapper):
        """ clears the recorded data from the object

        :param buffer_manager: the buffer manager object
        :param placements: the placements object
        :param graph_mapper: the graph mapper object
        :rtype: None
        """

    @abstractmethod
    def get_v(
            self, n_machine_time_steps, placements, graph_mapper,
            buffer_manager, machine_time_step):
        """ Get the recorded v from the object

        :param n_machine_time_steps: the number of timer ticks that will\
                be executed on the machine.
        :param placements: The placements of the graph
        :param graph_mapper: The mapper between vertices and vertices
        :param buffer_manager: the buffer manager object
        :param machine_time_step: the time step of the simulation
        :return: A numpy array of 3-element arrays of (neuron_id, time, v)\
                ordered by time
        """
