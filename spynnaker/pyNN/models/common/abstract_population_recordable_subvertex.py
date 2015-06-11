from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractPopulationRecordableSubvertex(object):

    @abstractmethod
    def get_v_recording_region(self):
        """ Get the region into which membrane voltage is recorded
        """

    @abstractmethod
    def get_gsyn_recording_region(self):
        """ Get the region
        """