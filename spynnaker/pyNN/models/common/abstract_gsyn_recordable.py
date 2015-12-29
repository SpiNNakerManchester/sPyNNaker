from abc import ABCMeta
from abc import abstractmethod

from six import add_metaclass

from spinn_front_end_common.interface.abstract_recordable_interface import \
    AbstractRecordableInterface


@add_metaclass(ABCMeta)
class AbstractGSynRecordable(AbstractRecordableInterface):
    """ Indicates that conductance can be recorded from this object
    """

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
    def get_gsyn(self, n_machine_time_steps, placements, graph_mapper,
                 buffer_manager):
        """ Get the recorded gsyn from the object

        :param n_machine_time_steps: the number of timer ticks that will\
                be executed on the machine.
        :param placements: The placements of the graph
        :param graph_mapper: The mapper between subvertices and vertices
        :param buffer_manager: the buffer manager object
        :return: A numpy array of 4-element arrays of \
                (neuron_id, time, gsyn_E, gsyn_I)\
                ordered by time
        """
