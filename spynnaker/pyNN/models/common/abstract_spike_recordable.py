# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.require_subclass import require_subclass
from pacman.model.graphs.application import ApplicationVertex


@require_subclass(ApplicationVertex)
class AbstractSpikeRecordable(object, metaclass=AbstractBase):
    """ Indicates that spikes can be recorded from this object.
    """

    __slots__ = ()

    @abstractmethod
    def is_recording_spikes(self):
        """ Determine if spikes are being recorded

        :return: True if spikes are being recorded, False otherwise
        :rtype: bool
        """

    @abstractmethod
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        """ Set spikes to being recorded. \
            If `new_state` is false all other parameters are ignored.

        :param bool new_state: Set if the spikes are recording or not
        :param sampling_interval: The interval at which spikes are recorded.
            Must be a whole multiple of the timestep.
            None will be taken as the timestep.
        :type sampling_interval: int or None
        :param indexes: The indexes of the neurons that will record spikes.
            If None the assumption is all neurons are recording
        :type indexes: list(int) or None
        """

    @abstractmethod
    def clear_spike_recording(self):
        """ Clear the recorded data from the object

        :rtype: None
        """

    @abstractmethod
    def get_spikes(self):
        """ Get the recorded spikes from the object

        :return: A numpy array of 2-element arrays of (neuron_id, time)
            ordered by time, one element per event
        :rtype: ~numpy.ndarray(tuple(int,int))
        """

    @abstractmethod
    def get_spikes_sampling_interval(self):
        """ Return the current sampling interval for spikes

        :return: Sampling interval in microseconds
        :rtype: float
        """

    @abstractmethod
    def write_spike_metadata(self):
        """ TODO """
