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
class AbstractNeuronRecordable(object, metaclass=AbstractBase):
    """ Indicates that a variable (e.g., membrane voltage) can be recorded\
        from this object.
    """

    __slots__ = ()

    @abstractmethod
    def get_recordable_variables(self):
        """ Returns a list of the PyNN names of variables this model is \
            expected to collect

        :rtype: list(str)
        """

    @abstractmethod
    def is_recording(self, variable):
        """ Determines if variable is being recorded.

        :param str variable: PyNN name of the variable
        :return: True if variable are being recorded, False otherwise
        :rtype: bool
        """

    @abstractmethod
    def set_recording(self, variable, new_state=True, sampling_interval=None,
                      indexes=None):
        """ Sets variable to being recorded

        :param str variable: PyNN name of the variable
        :param bool new_state:
        :param sampling_interval:
        :type sampling_interval: int or None
        :param indexes: Which indices are to be recorded (or None for all)
        :type indexes: list or None
        """

    @abstractmethod
    def clear_recording(self, variable, buffer_manager):
        """ Clear the recorded data from the object

        :param str variable: PyNN name of the variable
        :param buffer_manager: the buffer manager object
        :type buffer_manager:
            ~spinn_front_end_common.interface.buffer_management.BufferManager
        :rtype: None
        """

    @abstractmethod
    def get_data(self, variable, n_machine_time_steps, buffer_manager):
        """ Get the recorded data

        :param str variable: PyNN name of the variable
        :param int n_machine_time_steps:
        :param buffer_manager:
        :type buffer_manager:
            ~spinn_front_end_common.interface.buffer_management.BufferManager
        :return: (data, recording_indices, sampling_interval)
        :rtype: tuple(~numpy.ndarray,list(int),float)
        """
        # pylint: disable=too-many-arguments

    @abstractmethod
    def get_neuron_sampling_interval(self, variable):
        """ Returns the current sampling interval for this variable

        :param str variable: PyNN name of the variable
        :return: Sampling interval in microseconds
        :rtype: float
        """
