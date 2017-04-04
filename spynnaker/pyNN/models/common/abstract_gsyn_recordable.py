from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractGSynRecordable(object):
    """ Indicates that conductance can be recorded from this object
    """

    __slots__ = ()

    @abstractmethod
    def is_recording_gsyn(self):
        """ Determines if gsyn us being recorded

        :return: True if gsyn is being recorded, False otherwise
        :rtype: bool
        """

    @abstractmethod
    def set_recording_gsyn(self):
        """ Sets gsyn to being recorded
        """

    @abstractmethod
    def get_gsyn(
            self, n_machine_time_steps, placements, graph_mapper,
            buffer_manager, machine_time_step):
        """ Get the recorded gsyn from the object

        :param n_machine_time_steps: the number of timer ticks that will\
                be executed on the machine.
        :param placements: The placements of the graph
        :param graph_mapper: The mapper between vertices and vertices
        :param buffer_manager: the buffer manager object
        :param machine_time_step: the time step of the simulation
        :return: A numpy array of 4-element arrays of \
                (neuron_id, time, gsyn_E, gsyn_I)\
                ordered by time
        """
