from spynnaker.pyNN.exceptions import ExecutableFailedToStartException

from spinnman.transceiver import create_transceiver_from_hostname
from spinnman.data.file_data_reader import FileDataReader
from spinnman.model.cpu_state import CPUState

from pacman.utilities.progress_bar import ProgressBar

import time
from spinnman.messages.scp.scp_signal import SCPSignal


class Reload(object):
    """ Reload functions for reload scripts
    """

    def __init__(self, machine_name, version, app_id=30):
        self._transceiver = create_transceiver_from_hostname(machine_name,
                                                             discover=False)
        self._transceiver.ensure_board_is_ready(version)
        self._transceiver.discover_scamp_connections()
        self._transceiver.enable_dropped_packet_reinjection()
        self._app_id = app_id
        self._total_processors = 0

    def reload_application_data(self, reload_application_data_items,
                                load_data=True):
        progress = ProgressBar(len(reload_application_data_items),
                               "Reloading Application Data")
        for reload_application_data in reload_application_data_items:
            if load_data:
                data_file = FileDataReader(reload_application_data.data_file)
                self._transceiver.write_memory(
                    reload_application_data.chip_x,
                    reload_application_data.chip_y,
                    reload_application_data.base_address, data_file,
                    reload_application_data.data_size)
                data_file.close()
            user_0_register_address = \
                self._transceiver.get_user_0_register_address_from_core(
                    reload_application_data.chip_x,
                    reload_application_data.chip_y,
                    reload_application_data.processor_id)
            self._transceiver.write_memory(
                reload_application_data.chip_x, reload_application_data.chip_y,
                user_0_register_address, reload_application_data.base_address)
            progress.update()
            self._total_processors += 1
        progress.end()

    def reload_routes(self, reload_routing_tables):
        progress = ProgressBar(len(reload_routing_tables),
                               "Reloading Routing Tables")
        for reload_routing_table in reload_routing_tables:
            routing_table = reload_routing_table.routing_table
            self._transceiver.load_multicast_routes(
                routing_table.x, routing_table.y,
                routing_table.multicast_routing_entries, self._app_id)
            progress.update()
        progress.end()

    def reload_binaries(self, reload_binaries):
        progress = ProgressBar(len(reload_binaries), "Reloading Binaries")
        for binary in reload_binaries:
            binary_file = FileDataReader(binary.binary_path)
            self._transceiver.execute_flood(
                binary.core_subsets, binary_file, self._app_id,
                binary.binary_size)
            binary_file.close()
            progress.update()
        progress.end()

    def reload_ip_tags(self, ip_tags):
        for ip_tag in ip_tags:
            self._transceiver.set_ip_tag(ip_tag)

    def reload_reverse_ip_tags(self, reverse_ip_tags):
        for reverse_ip_tag in reverse_ip_tags:
            self._transceiver.set_reverse_ip_tag(reverse_ip_tag)

    def restart(self):
        processor_c_main = self._transceiver.get_core_state_count(
            self._app_id, CPUState.C_MAIN)

        # check that everything has gone though c main to reach sync0 or
        # failing for some unknown reason
        while processor_c_main != 0:
            time.sleep(0.1)
            processor_c_main = self._transceiver.get_core_state_count(
                self._app_id, CPUState.C_MAIN)

        # check that the right number of processors are in sync0
        processors_ready = self._transceiver.get_core_state_count(
            self._app_id, CPUState.SYNC0)

        if processors_ready < self._total_processors:
            raise ExecutableFailedToStartException(
                "Only {} processors out of {} have sucessfully reached sync0"
                .format(processors_ready, self._total_processors))

        # Send SYNC0
        self._transceiver.send_signal(self._app_id, SCPSignal.SYNC0)
