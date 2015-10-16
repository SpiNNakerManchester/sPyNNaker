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
