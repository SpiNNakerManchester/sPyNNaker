from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractGSynRecordable(object):
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
    def reset(self):
        """
        closes the cahce file this vertex uses for storing its gsyn data
        :return:
        """

    @abstractmethod
    def get_gsyn(self, transceiver, n_machine_time_steps, placements,
                 graph_mapper, return_data):
        """ Get the recorded gsyn from the object
        :param transceiver: the python interface to the spinnaker machine
        :param n_machine_time_steps: the number of timer tics that will
        be exeucted on the machine.

        :return: A numpy array of 4-element arrays of \
                (neuron_id, time, gsyn_E, gsyn_I)\
                ordered by time
        """
