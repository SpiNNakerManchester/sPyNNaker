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


class VariableCache(object):
    """ Simple holder method to keep data, IDs, indexes and units together

    Typically used to recreate the Neo object for one type of variable for\
    one segment
    """
    __slots__ = ("__data", "__indexes", "__n_neurons", "__sampling_interval",
                 "__units")

    def __init__(self, data, indexes, n_neurons, units, sampling_interval):
        """
        :param data: raw data in sPyNNaker format
        :type data: nparray
        :param indexes: Population indexes for which data was collected
        :type indexes: list (int)
        :param n_neurons: Number of neurons in the population,\
            regardless of whether they were recording or not.
        :type n_neurons: int
        :param units: the units in which the data is
        :type units: str
        """
        self.__data = data
        self.__indexes = indexes
        self.__n_neurons = n_neurons
        self.__units = units
        self.__sampling_interval = sampling_interval

    @property
    def data(self):
        return self.__data

    @property
    def indexes(self):
        return self.__indexes

    @property
    def n_neurons(self):
        return self.__n_neurons

    @property
    def units(self):
        return self.__units

    @property
    def sampling_interval(self):
        return self.__sampling_interval
