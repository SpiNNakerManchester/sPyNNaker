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
    def get_gsyn(self, transceiver, n_machine_time_steps):
        """ Get the recorded gsyn from the object

        :return: A numpy array of 4-element arrays of \
                (neuron_id, time, gsyn_E, gsyn_I)\
                ordered by time
        """
