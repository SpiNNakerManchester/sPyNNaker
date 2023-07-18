# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
from typing import Dict, Iterable, Optional, Tuple
from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utilities.connections.live_event_connection \
    import (
        LiveEventConnection, _Callback, _InitCallback)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities.constants import NOTIFY_PORT


class SpynnakerPoissonControlConnection(LiveEventConnection):
    """
    A connection used to control a Poisson-distributed random event source's
    firing rate at runtime.
    """
    __slots__ = (
        "__control_label_extension",
        "__control_label_to_label",
        "__label_to_control_label")

    def __init__(
            self, poisson_labels: Optional[Iterable[str]] = None,
            local_host: Optional[str] = None,
            local_port: Optional[int] = NOTIFY_PORT,
            control_label_extension: str = "_control"):
        """
        :param iterable(str) poisson_labels:
            Labels of Poisson populations to be controlled
        :param str local_host: Optional specification of the local hostname or
            IP address of the interface to listen on
        :param int local_port:
            Optional specification of the local port to listen on. Must match
            the port that the toolchain will send the notification on (19999
            by default)
        :param str control_label_extension:
            The extra name added to the label of each Poisson source
        """
        self.__control_label_extension = control_label_extension

        control_labels: Optional[Iterable[str]] = None
        self.__control_label_to_label: Dict[str, str] = dict()
        self.__label_to_control_label: Dict[str, str] = dict()
        if poisson_labels is not None:
            control_labels = [
                self.__convert_to_control_label(label)
                for label in poisson_labels
            ]
            self.__control_label_to_label.update(
                {control: label
                 for control, label in zip(control_labels, poisson_labels)})
            self.__label_to_control_label.update(
                {label: control
                 for label, control in zip(poisson_labels, control_labels)})

        super().__init__(
            live_packet_gather_label=None, send_labels=control_labels,
            local_host=local_host, local_port=local_port)

    def add_poisson_label(self, label: str):
        """
        :param str label: The label of the Poisson source population.
        """
        control = self.__convert_to_control_label(label)
        self.__control_label_to_label[control] = label
        self.__label_to_control_label[label] = control
        self.add_send_label(control)

    def __convert_to_control_label(self, label: str) -> str:
        return f"{label}{self.__control_label_extension}"

    def __control_label(self, label: str) -> str:
        # Try to get a control label, but if not just use the label
        return self.__label_to_control_label.get(label, label)

    def __label(self, control_label: str) -> str:
        # Try to get a label, but if not just use the control label
        return self.__control_label_to_label.get(control_label, control_label)

    def __callback_wrapper(
            self, callback: _Callback, label: str,
            connection: LiveEventConnection):
        callback(self.__label(label), connection)

    def __init_callback_wrapper(
            self, callback: _InitCallback,
            label: str, vertex_size: int, run_time_ms: float,
            machine_timestep_ms: float):
        callback(self.__label(label), vertex_size, run_time_ms,
                 machine_timestep_ms)

    @overrides(LiveEventConnection.add_start_callback)
    def add_start_callback(self, label: str, start_callback: _Callback):
        super().add_start_callback(
            self.__control_label(label), functools.partial(
                self.__callback_wrapper, start_callback))

    @overrides(LiveEventConnection.add_start_resume_callback)
    def add_start_resume_callback(
            self, label: str, start_resume_callback: _Callback):
        super().add_start_resume_callback(
            self.__control_label(label), functools.partial(
                self.__callback_wrapper, start_resume_callback))

    @overrides(LiveEventConnection.add_init_callback)
    def add_init_callback(self, label: str, init_callback: _InitCallback):
        super().add_init_callback(
            self.__control_label(label), functools.partial(
                self.__init_callback_wrapper, init_callback))

    @overrides(LiveEventConnection.add_receive_callback)
    def add_receive_callback(self, label, live_event_callback, *,
                             translate_key=False, for_times=False):
        raise ConfigurationException(
            "SpynnakerPoissonControlPopulation can't receive data")

    @overrides(LiveEventConnection.add_pause_stop_callback)
    def add_pause_stop_callback(
            self, label: str, pause_stop_callback: _Callback):
        super().add_pause_stop_callback(
            self.__control_label(label), functools.partial(
                self.__callback_wrapper, pause_stop_callback))

    def set_rate(self, label: str, neuron_id: int, rate: float):
        """
        Set the rate of a Poisson neuron within a Poisson source.

        :param str label: The label of the Population to set the rates of
        :param int neuron_id: The neuron ID to set the rate of
        :param float rate: The rate to set in Hz
        """
        self.set_rates(label, [(neuron_id, rate)])

    def set_rates(
            self, label: str, neuron_id_rates: Iterable[Tuple[int, float]]):
        """
        Set the rates of multiple Poisson neurons within a Poisson source.

        :param str label: The label of the Population to set the rates of
        :param list(tuple(int,float)) neuron_id_rates:
            A list of tuples of (neuron ID, rate) to be set
        """
        control = self.__control_label(label)
        datatype = DataType.S1615
        atom_ids_and_payloads = [(nid, datatype.encode_as_int(rate))
                                 for nid, rate in neuron_id_rates]
        self.send_events_with_payloads(control, atom_ids_and_payloads)
