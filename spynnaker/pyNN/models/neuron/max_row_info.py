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


class MaxRowInfo(object):
    """ Information about the maximums for rows in a synaptic matrix.
    """

    __slots__ = [
        "__undelayed_max_n_synapses",
        "__delayed_max_n_synapses",
        "__undelayed_max_bytes",
        "__delayed_max_bytes",
        "__undelayed_max_words",
        "__delayed_max_words",
    ]

    def __init__(
            self, undelayed_max_n_synapses, delayed_max_n_synapses,
            undelayed_max_bytes, delayed_max_bytes,
            undelayed_max_words, delayed_max_words):
        self.__undelayed_max_n_synapses = undelayed_max_n_synapses
        self.__delayed_max_n_synapses = delayed_max_n_synapses
        self.__undelayed_max_bytes = undelayed_max_bytes
        self.__delayed_max_bytes = delayed_max_bytes
        self.__undelayed_max_words = undelayed_max_words
        self.__delayed_max_words = delayed_max_words

    @property
    def undelayed_max_n_synapses(self):
        return self.__undelayed_max_n_synapses

    @property
    def delayed_max_n_synapses(self):
        return self.__delayed_max_n_synapses

    @property
    def undelayed_max_bytes(self):
        return self.__undelayed_max_bytes

    @property
    def delayed_max_bytes(self):
        return self.__delayed_max_bytes

    @property
    def undelayed_max_words(self):
        return self.__undelayed_max_words

    @property
    def delayed_max_words(self):
        return self.__delayed_max_words
