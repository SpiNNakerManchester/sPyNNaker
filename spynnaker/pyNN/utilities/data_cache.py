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

from datetime import datetime
from .variable_cache import VariableCache


class DataCache(object):
    """ Storage object to hold all the data to (re)create a Neo Segment

    .. note::
        Required because deep-copy does not work on neo Objects

    Stores the Data shared by all variable types at the top level
    and holds a cache for the variable specific data.
    """

    __slots__ = ("__cache",
                 "__description",
                 "__label",
                 "__rec_datetime",
                 "__recording_start_time",
                 "__segment_number",
                 "__t")

    def __init__(self, label, description, segment_number,
                 recording_start_time, t):
        """
        :param str label: cache label
        :param description: cache description
        :type description: str or dict
        :param int segment_number: cache segment number
        :param float recording_start_time:
            when this cache was started in recording space.
        :param float t: time
        """
        # pylint: disable=too-many-arguments
        self.__label = label
        self.__description = description
        self.__segment_number = segment_number
        self.__recording_start_time = recording_start_time
        self.__t = t
        self.__cache = dict()
        self.__rec_datetime = None

    @property
    def variables(self):
        """ Provides a list of which variables data has been cached for

        :rtype: Iterator (str)
        """
        return self.__cache.keys()

    @property
    def label(self):
        return self.__label

    @property
    def description(self):
        return self.__description

    @property
    def segment_number(self):
        return self.__segment_number

    @property
    def recording_start_time(self):
        return self.__recording_start_time

    @property
    def t(self):
        return self.__t

    @property
    def rec_datetime(self):
        return self.__rec_datetime

    def has_data(self, variable):
        """ Checks if data for a variable has been cached

        :param str variable: Name of variable
        :return: True if there is cached data
        :rtype: bool
        """
        return variable in self.__cache

    def get_data(self, variable):
        """ Get the variable cache for the named variable

        :param str variable: name of variable to get cache for
        :return: The cache data, IDs, indexes and units
        :rtype: VariableCache
        """
        return self.__cache[variable]

    def save_data(self, variable, data, indexes, n_neurons, units,
                  sampling_interval):
        """ Saves the data for one variable in this segment

        :param str variable: name of variable data applies to
        :param ~numpy.ndarray data: raw data in sPyNNaker format
        :param ~numpy.ndarray indexes:
            population indexes for which data should be returned
        :param int n_neurons: Number of neurons in the population,
            regardless of if they where recording or not.
        :param str units: the units in which the data is
        :param sampling_interval: The number of milliseconds between samples.
        :type sampling_interval: float or int
        """
        self.__rec_datetime = datetime.now()
        variable_cache = VariableCache(
            data, indexes, n_neurons, units, sampling_interval)
        self.__cache[variable] = variable_cache
