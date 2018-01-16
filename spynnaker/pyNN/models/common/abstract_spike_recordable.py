from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractSpikeRecordable(object):
    """ Indicates that spikes can be recorded from this object
    """

    __slots__ = ()

    @abstractmethod
    def is_recording_spikes(self):
        """ Determines if spikes are being recorded

        :return: True if spikes are being recorded, False otherwise
        :rtype: bool
        """

    @abstractmethod
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        """ Sets spikes to being recorded

        If new_state is false all other paramteres are ignored.

        :param new_state: Set if the spikes are recording or not
        :type new_state: bool
        :param sampling_interval: The interval at which spikes are recorded.\
            Must be a whole multiple of the timestep
            None will be taken as the timestep
        :param indexes: The indexes of the neurons that will record spikes.
            If None the assumption is all neurons are recording
        """

    @abstractmethod
    def clear_spike_recording(self, buffer_manager, placements, graph_mapper):
        """ clears the recorded data from the object

        :param buffer_manager: the buffer manager object
        :param placements: the placements object
        :param graph_mapper: the graph mapper object
        :rtype: None
        """

    @abstractmethod
    def get_spikes(
            self, placements, graph_mapper, buffer_manager, machine_time_step):
        """ Get the recorded spikes from the object

        :param placements: the placements object
        :param graph_mapper: the graph mapper object
        :param buffer_manager: the buffer manager object
        :param machine_time_step: the time step of the simulation
        :return: A numpy array of 2-element arrays of (neuron_id, time)\
                ordered by time
        """

    @abstractmethod
    def get_spikes_sampling_interval(self):
        """ Returns the current sampling interval for spikes
        :return: Sampling interval in micro seconds

        if self.is_recording_spikes():
            return globals_variables.get_simulator().machine_time_step / 1000
        else:
            return 0
        """