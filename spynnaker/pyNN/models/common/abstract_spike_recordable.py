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
    def get_last_extracted_spike_time(self):
        """ gets the last time point which the vertex thinks its extracted from
        the machine
        :return:
        """

    @abstractmethod
    def set_last_extracted_spike_time(self, new_value):
        """ sets the last time point which the vertex thinks its extracted from
        the machine
        :param new_value: the new value for the last_extracted_spike_time
        :return:
        """

    @abstractmethod
    def get_cache_file_for_spike_data(self):
        """
        gets the cahce file this vertex uses for storing its spike data
        :return:
        """

    @abstractmethod
    def close_cache_file_for_spike_data(self):
        """
        closes the cahce file this vertex uses for storing its spike data
        :return:
        """

    @abstractmethod
    def get_spikes(self, transceiver, n_machine_time_steps, placements,
                   graph_mapper):
        """ Get the recorded spikes from the object
        :param transceiver: the python interface to the spinnaker machine
        :param n_machine_time_steps: the number of machine time steps the
        system expects to run
        :param placements: the placements object
        :param graph_mapper: the graph mapper object
        :return: A numpy array of 2-element arrays of (neuron_id, time)\
                ordered by time
        """
