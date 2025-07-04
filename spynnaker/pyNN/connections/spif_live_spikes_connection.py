# Copyright (c) 2022 The University of Manchester
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

import logging
import struct
from threading import Thread
from typing import Callable, Dict, Final, Iterable, List, Optional, Set, Tuple
from typing_extensions import TypeAlias
from spinn_utilities.log import FormatAdapter
from spinnman.connections import ConnectionListener
from spinnman.connections.udp_packet_connections import UDPConnection
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.utilities.database import DatabaseConnection
from spinn_front_end_common.utilities.database import DatabaseReader

_EVENT: Final['TypeAlias'] = Callable[[str, List[int]], None]
_INIT: Final['TypeAlias'] = Callable[[str, int, float, float], None]
_START_STOP: Final['TypeAlias'] = Callable[
    [str, 'SPIFLiveSpikesConnection'], None]
logger = FormatAdapter(logging.getLogger(__name__))

_TWO_SKIP = struct.Struct("<2x")

_THREE_INTS = struct.Struct("<3I")

_ONE_INT = struct.Struct("<I")

# The port that SPIF listens on by default
_DEFAULT_SPIF_PORT = 3332

# The maximum number of events in each packet by default
_EVENTS_PER_PACKET = 32

# The maximum time between packets in microseconds by default
_US_PER_PACKET = 500

# SPIF message to start sending
_SPIF_OUTPUT_START = 0x5ec00000

# SPIF message to stop sending
_SPIF_OUTPUT_STOP = 0x5ec10000

# SPIF message to set packet send time (time is added to this in microseconds)
_SPIF_OUTPUT_SET_TICK = 0x5ec20000

# SPIF message to set packet size (size is added to this in bytes)
_SPIF_OUTPUT_SET_LEN = 0x5ec40000


class SPIFLiveSpikesConnection(DatabaseConnection):
    """
    A connection for receiving live spikes from SPIF.
    """
    # TODO: define SPIF
    __slots__ = (
        "__error_keys",
        "__init_callbacks",
        "__key_to_atom_id_and_label",
        "__live_event_callbacks",
        "__pause_stop_callbacks",
        "__receive_labels",
        "__receiver_connection",
        "__receiver_listener",
        "__start_resume_callbacks",
        "__spif_host",
        "__spif_port",
        "__spif_packet_size",
        "__spif_packet_time_us")

    def __init__(self, receive_labels: Optional[Iterable[str]],
                 spif_host: str, spif_port: int = _DEFAULT_SPIF_PORT,
                 events_per_packet: int = _EVENTS_PER_PACKET,
                 time_per_packet: int = _US_PER_PACKET,
                 local_host: Optional[str] = None,
                 local_port: Optional[int] = None):
        """
        :param receive_labels:
            Labels of vertices from which live events will be received.
        :param spif_host: The location of the SPIF board receiving packets
        :param spif_port: The port of the SPIF board (default 3332)
        :param events_per_packet:
            The maximum number of events in each packet.  SPIF will be
            configured to send a packet as soon as it reaches this size if not
            before (default is 32)
        :param time_per_packet:
            The maximum time between sending non-empty packets.  SPIF will be
            configured to send a packet that isn't empty after this many
            microseconds (default is 500)
        :param local_host:
            Optional specification of the local hostname or IP address of the
            interface to listen on
        :param local_port:
            Optional specification of the local port to listen on. Must match
            the port that the toolchain will send the notification on (19999
            by default)
        """
        super().__init__(
            self.__do_start_resume, self.__do_stop_pause,
            local_host=local_host, local_port=local_port)

        self.add_database_callback(self.__read_database_callback)

        self.__receive_labels = (
            list(receive_labels) if receive_labels is not None else [])

        self.__spif_host = spif_host
        self.__spif_port = spif_port
        self.__spif_packet_size = events_per_packet * BYTES_PER_WORD
        self.__spif_packet_time_us = time_per_packet
        self.__key_to_atom_id_and_label: Dict[int, Tuple[int, int]] = dict()
        self.__live_event_callbacks: List[List[Tuple[_EVENT, bool]]] = list()
        self.__start_resume_callbacks: Dict[str, List[_START_STOP]] = dict()
        self.__pause_stop_callbacks: Dict[str, List[_START_STOP]] = dict()
        self.__init_callbacks: Dict[str, List[_INIT]] = dict()
        if receive_labels is not None:
            for label in receive_labels:
                self.__live_event_callbacks.append(list())
                self.__start_resume_callbacks[label] = list()
                self.__pause_stop_callbacks[label] = list()
                self.__init_callbacks[label] = list()
        self.__receiver_listener: Optional[ConnectionListener[bytes]] = None
        self.__receiver_connection: Optional[UDPConnection] = None
        self.__error_keys: Set[int] = set()

    def add_receive_label(self, label: str) -> None:
        """
        :param label:
        """
        if label not in self.__receive_labels:
            self.__receive_labels.append(label)
            self.__live_event_callbacks.append(list())
        if label not in self.__start_resume_callbacks:
            self.__start_resume_callbacks[label] = list()
            self.__pause_stop_callbacks[label] = list()
            self.__init_callbacks[label] = list()

    def add_init_callback(self, label: str, init_callback: _INIT) -> None:
        """
        Add a callback to be called to initialise a vertex.

        :param label:
            The label of the vertex to be notified about. Must be one of the
            vertices listed in the constructor
        :param init_callback: A function to be called to initialise the
            vertex. This should take as parameters the label of the vertex,
            the number of neurons in the population, the run time of the
            simulation in milliseconds, and the simulation timestep in
            milliseconds
        """
        self.__init_callbacks[label].append(init_callback)

    def add_receive_callback(
            self, label: str, live_event_callback: _EVENT,
            translate_key: bool = True) -> None:
        """
        Add a callback for the reception of live events from a vertex.

        :param label: The label of the vertex to be notified about.
            Must be one of the vertices listed in the constructor
        :param live_event_callback: A function to be called when events are
            received. This should take as parameters the label of the vertex,
            and an array-like of atom IDs.
        :param translate_key:
            True if the key is to be converted to an atom ID, False if the
            key should stay a key
        """
        label_id = self.__receive_labels.index(label)
        logger.info(
            "Receive callback {} registered to label {}",
            live_event_callback, label)
        self.__live_event_callbacks[label_id].append(
            (live_event_callback, translate_key))

    def add_start_resume_callback(
            self, label: str, start_resume_callback: _START_STOP) -> None:
        """
        Add a callback for the start and resume state of the simulation.

        :param label: the label of the function to be sent
        :param start_resume_callback: A function to be called when the start
            or resume message has been received. This function should take
            the label of the referenced vertex, and an instance of this
            class, which can be used to send events.
        """
        self.__start_resume_callbacks[label].append(start_resume_callback)

    def add_pause_stop_callback(
            self, label: str, pause_stop_callback: _START_STOP) -> None:
        """
        Add a callback for the pause and stop state of the simulation.

        :param label: the label of the function to be sent
        :param pause_stop_callback: A function to be called when the pause
            or stop message has been received. This function should take the
            label of the referenced  vertex, and an instance of this class,
            which can be used to send events.
        """
        self.__pause_stop_callbacks[label].append(pause_stop_callback)

    def __read_database_callback(self, db_reader: DatabaseReader) -> None:
        self.__handle_possible_rerun_state()

        vertex_sizes: Dict[str, int] = dict()
        run_time_ms = db_reader.get_configuration_parameter_value(
            "runtime") or 0.0
        machine_timestep_ms = (
            db_reader.get_configuration_parameter_value("machine_time_step")
            or 0.0) / 1000.0

        if self.__receive_labels:
            self.__init_receivers(db_reader, vertex_sizes)

        for label, vertex_size in vertex_sizes.items():
            for init_callback in self.__init_callbacks[label]:
                init_callback(
                    label, vertex_size, run_time_ms, machine_timestep_ms)

    def __init_receivers(
            self, db: DatabaseReader, vertex_sizes: Dict[str, int]) -> None:
        # Set up a single connection for receive
        if self.__receiver_connection is None:
            self.__receiver_connection = UDPConnection(
                remote_host=self.__spif_host, remote_port=self.__spif_port)
        for label_id, label in enumerate(self.__receive_labels):
            key_to_atom_id = db.get_key_to_atom_id_mapping(label)
            for key, atom_id in key_to_atom_id.items():
                self.__key_to_atom_id_and_label[key] = (atom_id, label_id)
            vertex_sizes[label] = len(key_to_atom_id)

        # Last of all, set up the listener for packets
        # NOTE: Has to be done last as otherwise will receive SCP messages
        # sent above!
        if self.__receiver_listener is None:
            self.__receiver_listener = ConnectionListener(
                self.__receiver_connection)
            self.__receiver_listener.add_callback(self.__do_receive_packet)
            self.__receiver_listener.start()

    def __handle_possible_rerun_state(self) -> None:
        # reset from possible previous calls
        if self.__receiver_listener is not None:
            self.__receiver_listener.close()
            self.__receiver_listener = None
        if self.__receiver_connection is not None:
            self.__receiver_connection.close()
            self.__receiver_connection = None

    def __launch_thread(
            self, kind: str, label: str, callback: _START_STOP) -> None:
        thread = Thread(target=callback, args=(label, self), name=(
            f"{kind} callback thread for live_event_connection "
            f"{self._local_port}:{self._local_ip_address}"))
        thread.start()

    def __do_start_resume(self) -> None:
        if not self.__receiver_connection:
            return
        # Send SPIF configuration
        self.__receiver_connection.send(_THREE_INTS.pack(
            _SPIF_OUTPUT_SET_LEN + self.__spif_packet_size,
            _SPIF_OUTPUT_SET_TICK + self.__spif_packet_time_us,
            _SPIF_OUTPUT_START))
        for label, callbacks in self.__start_resume_callbacks.items():
            for callback in callbacks:
                self.__launch_thread("start_resume", label, callback)

    def __do_stop_pause(self) -> None:
        if not self.__receiver_connection:
            return
        # Stop SPIF output
        self.__receiver_connection.send(_ONE_INT.pack(_SPIF_OUTPUT_STOP))
        for label, callbacks in self.__pause_stop_callbacks.items():
            for callback in callbacks:
                self.__launch_thread("pause_stop", label, callback)

    def __do_receive_packet(self, packet: bytes) -> None:
        # pylint: disable=broad-except
        logger.debug("Received packet")
        try:
            self.__handle_packet(packet)
        except Exception:
            logger.warning("problem handling received packet", exc_info=True)

    def __handle_packet(self, packet: bytes) -> None:
        key_labels: Dict[int, List[int]] = dict()
        atoms_labels: Dict[int, List[int]] = dict()
        n_events = len(packet) // BYTES_PER_WORD
        events = struct.unpack(f"<{n_events}I", packet)
        for key in events:
            if key in self.__key_to_atom_id_and_label:
                atom_id, label_id = self.__key_to_atom_id_and_label[key]
                if label_id not in key_labels:
                    key_labels[label_id] = list()
                    atoms_labels[label_id] = list()
                key_labels[label_id].append(key)
                atoms_labels[label_id].append(atom_id)
            else:
                self.__handle_unknown_key(key)

        for label_id in key_labels:
            label = self.__receive_labels[label_id]
            for c_back, use_atom in self.__live_event_callbacks[label_id]:
                if use_atom:
                    c_back(label, atoms_labels[label_id])
                else:
                    c_back(label, key_labels[label_id])

    def __handle_unknown_key(self, key: int) -> None:
        if key not in self.__error_keys:
            self.__error_keys.add(key)
            logger.warning("Received unexpected key {}", key)
