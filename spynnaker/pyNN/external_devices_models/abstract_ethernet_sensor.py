# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
