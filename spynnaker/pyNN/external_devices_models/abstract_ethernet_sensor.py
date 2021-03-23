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


class AbstractEthernetSensor(object, metaclass=AbstractBase):
    __slots__ = []

    @abstractmethod
    def get_n_neurons(self):
        """ Get the number of neurons that will be sent out by the device

        :rtype: int
        """

    @abstractmethod
    def get_injector_parameters(self):
        """ Get the parameters of the Spike Injector to use with this device

        :rtype: dict(str,Any)
        """

    @abstractmethod
    def get_injector_label(self):
        """ Get the label to give to the Spike Injector

        :rtype: str
        """

    @abstractmethod
    def get_translator(self):
        """ Get a translator of multicast commands to Ethernet commands

        :rtype: AbstractEthernetTranslator
        """

    @abstractmethod
    def get_database_connection(self):
        """ Get a Database Connection instance that this device uses\
            to inject packets

        :rtype: ~spynnaker.pyNN.connections.SpynnakerLiveSpikesConnection
        """
