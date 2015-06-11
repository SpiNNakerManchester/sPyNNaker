from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSpikeRecordableSubvertex(object):
    """ A subvertex of an AbstractSpikeRecordableVertex
    """

    @abstractmethod
    def get_spike_recording_region(self):
        """ Get the region number which is used for recording spikes
        """
