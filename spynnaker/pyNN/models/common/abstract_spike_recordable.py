from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSpikeRecordable(object):
    """ Indicates that spikes can be recorded from this object
    """

    @abstractmethod
    def is_recording_spikes(self):
        """ Determines if spikes are being recorded

        :return: True if spikes are being recorded, False otherwise
        :rtype: bool
        """

    @abstractmethod
    def set_recording_spikes(self):
        """ Sets spikes to being recorded
        """

    @abstractmethod
    def get_spikes(self, placements, graph_mapper, buffer_manager):
        """ Get the recorded spikes from the object
        :param placements: the placements object
        :param graph_mapper: the graph mapper object
        :param buffer_manager: the buffer manager object
        :return: A numpy array of 2-element arrays of (neuron_id, time)\
                ordered by time
        """
