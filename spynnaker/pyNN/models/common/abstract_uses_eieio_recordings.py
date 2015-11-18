"""
AbstractEIEIOSpikeRecordable
"""
from six import add_metaclass
from abc import ABCMeta
from abc import abstractproperty


@add_metaclass(ABCMeta)
class AbstractUsesEIEIORecordings(object):
    """
    AbstractEIEIOSpikeRecordable: interface which covers the fact that eieio\
    recordable vertices need to have a base key for atoms, and needs to store
    the max size of the recording region\
    """

    @abstractproperty
    def base_key(self):
        """

        :return:
        """

    @abstractproperty
    def region_size(self):
        """

        :return:
        """
