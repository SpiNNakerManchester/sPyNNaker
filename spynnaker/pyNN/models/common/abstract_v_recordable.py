from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractVRecordable(object):
    """ Indicates that membrane voltage can be recorded from this object
    """

    @abstractmethod
    def is_recording_v(self):
        """ Determines if v is being recorded

        :return: True if v are being recorded, False otherwise
        :rtype: bool
        """

    @abstractmethod
    def set_recording_v(self):
        """ Sets v to being recorded
        """

    @abstractmethod
    def get_last_extracted_v_time(self):
        """ gets the last time point which the vertex thinks its extracted from
        the machine
        :return:
        """

    @abstractmethod
    def set_last_extracted_v_time(self, new_value):
        """ sets the last time point which the vertex thinks its extracted from
        the machine
        :param new_value: the new value to set the last_extracted_v_time
        :return:
        """

    @abstractmethod
    def get_cache_file_for_v_data(self):
        """
        gets the cahce file this vertex uses for storing its v data
        :return:
        """

    @abstractmethod
    def close_cache_file_for_v_data(self):
        """
        closes the cahce file this vertex uses for storing its v data
        :return:
        """

    @abstractmethod
    def get_v(self, transceiver, n_machine_time_steps, placements,
              graph_mapper):
        """ Get the recorded v from the object

        :param transceiver: the python interface to the spinnaker machine
        :param n_machine_time_steps: the number of timer tic exeuctions
        when running on the machine

        :return: A numpy array of 3-element arrays of (neuron_id, time, v)\
                ordered by time
        """
