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
class AbstractEventRecordable(object, metaclass=AbstractBase):
    """ Indicates that events can be recorded from this object.
    """

    __slots__ = ()

    @abstractmethod
    def is_recording_events(self, variable):
        """ Determine if events are being recorded

        :param str variable: The variable to check
        :return: True if events are recorded for the variable, False otherwise
        :rtype: bool
        """

    @abstractmethod
    def set_recording_events(
            self, variable, new_state=True, sampling_interval=None,
            indexes=None):
        """ Set events to being recorded. \
            If `new_state` is false all other parameters are ignored.

        :param str variable: The variable to set recording
        :param bool new_state: Set if the events are recording or not
        :param sampling_interval: The interval at which events are recorded.
            Must be a whole multiple of the timestep.
            None will be taken as the timestep.
        :type sampling_interval: int or None
        :param indexes: The indexes of the neurons that will record events.
            If None the assumption is all neurons are recording
        :type indexes: list(int) or None
        """

    @abstractmethod
    def clear_event_recording(self):
        """ Clear the recorded data from the object

        :rtype: None
        """

    @abstractmethod
    def get_events(self, variable):
        """ Get the recorded events from the object

        :param str variable: The variable to get the event data for
        :return: A numpy array of 2-element arrays of (neuron_id, time)
            ordered by time, one element per event
        :rtype: ~numpy.ndarray(tuple(int,int))
        """

    @abstractmethod
    def get_events_sampling_interval(self, variable):
        """ Return the current sampling interval for events

        :param str variable: The variable to get the sampling interval for
        :return: Sampling interval in microseconds
        :rtype: float
        """
