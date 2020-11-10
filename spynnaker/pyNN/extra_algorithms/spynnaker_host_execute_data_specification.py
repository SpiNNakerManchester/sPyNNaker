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

from collections import defaultdict

import datetime
import logging
import numpy
from six import iteritems, itervalues

from spinn_front_end_common.interface.interface_functions import \
    HostExecuteDataSpecification
from spinn_front_end_common.interface.interface_functions.host_execute_data_specification import \
    filter_out_system_executables, _MEM_REGIONS, system_cores, \
    filter_out_app_executables
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.log import FormatAdapter
from data_specification import DataSpecificationExecutor
from data_specification.exceptions import DataSpecificationException
from spinn_front_end_common.interface.ds.ds_write_info import DsWriteInfo
from spinn_front_end_common.utilities.helpful_functions import (
    write_address_to_user0)
from spinn_front_end_common.utilities.utility_objs import (
    ExecutableType, DataWritten)
from spinn_front_end_common.utilities.helpful_functions import (
    emergency_recover_states_from_failure)
from spinn_front_end_common.utilities import globals_variables, \
    helpful_functions
from spinn_utilities.timer import Timer
from spynnaker.pyNN.models.neuron import PopulationMachineVertex
from spynnaker.pyNN.models.utility_models.delays import \
    DelayExtensionMachineVertex
from spynnaker.pyNN.utilities.constants import POPULATION_BASED_REGIONS

logger = FormatAdapter(logging.getLogger(__name__))


class SpyNNakerHostExecuteDataSpecification(HostExecuteDataSpecification):
    """ Executes the host based data specification.
    """

    __slots__ = [
        # the application ID of the simulation
        "_app_id",
        "_core_to_conn_map",
        # The path where the SQLite database holding the data will be placed,
        # and where any java provenance can be written.
        "_db_folder",
        # The support class to run via Java. If None pure python is used.
        "_java",
        # The python representation of the SpiNNaker machine.
        "_machine",
        "_monitors",
        "_placements",
        # The spinnman instance.
        "_txrx",
        # The write info; a dict of cores to a dict of
        # 'start_address', 'memory_used', 'memory_written'
        "_write_info_map"]

    first = True

    def __init__(self):
        self._app_id = None
        self._core_to_conn_map = None
        self._db_folder = None
        self._java = None
        self._machine = None
        self._monitors = None
        self._placements = None
        self._txrx = None
        self._write_info_map = None

    def __java_database(self, dsg_targets, progress, region_sizes):
        """
        :param DataSpecificationTargets dsg_tagets:
        :param ~spinn_utilities.progress_bar.ProgressBar progress:
        :param dict(tuple(int,int,int)int) region_sizes:
        :rtype: DsWriteInfo
        """
        # Copy data from WriteMemoryIOData to database
        dw_write_info = DsWriteInfo(dsg_targets.get_database())
        dw_write_info.clear_write_info()
        if self._write_info_map is not None:
            for core, info in iteritems(self._write_info_map):
                (x, y, p) = core
                dw_write_info.set_info(x, y, p, info)
                del region_sizes[core]
        for core in region_sizes:
            (x, y, p) = core
            dw_write_info.set_size_info(x, y, p, region_sizes[core])
        progress.update()
        dsg_targets.set_app_id(self._app_id)
        self._java.set_machine(self._machine)
        self._java.set_report_folder(self._db_folder)
        progress.update()
        return dw_write_info

    def __java_all(self, dsg_targets, region_sizes):
        """ Does the Data Specification Execution and loading using Java

        :param DataSpecificationTargets dsg_targets:
            map of placement to file path
        :return: map of of cores to descriptions of what was written
        :rtype: DsWriteInfo
        """
        # create a progress bar for end users
        progress = ProgressBar(
            3, "Executing data specifications and loading data using Java")

        # Copy data from WriteMemoryIOData to database
        dw_write_info = self.__java_database(
            dsg_targets, progress, region_sizes)

        self._java.execute_data_specification()

        progress.end()
        return dw_write_info

    def __python_all(self, dsg_targets, region_sizes, placements):
        """ Does the Data Specification Execution and loading using Python

        :param Placements placements: placements
        :param DataSpecificationTargets dsg_targets:
            map of placement to file path
        :param dict(tuple(int,int,int),int) region_sizes:
            map between vertex and list of region sizes
        :return: dict of cores to descriptions of what was written
        :rtype: dict(tuple(int,int,int), DataWritten)
        """
        # While the database supports having the info in it a python bugs does
        # not like iterating over and writing intermingled so using a dict
        results = self._write_info_map
        if results is None:
            results = dict()

        # create a progress bar for end users
        progress = ProgressBar(
            dsg_targets.n_targets(),
            "Executing data specifications and loading data")

        # allocate and set user 0 before loading data
        base_addresses = dict()
        for core, _ in iteritems(dsg_targets):
            base_addresses[core] = self.__malloc_region_storage(
                core, region_sizes[core])

        for core, reader in progress.over(iteritems(dsg_targets)):
            x, y, p = core
            data_written, _matrix, _connection, _total, _executor, _time = \
                self.__python_execute(
                    core, reader, self._txrx.write_memory,
                    base_addresses[core], region_sizes[core],
                    placements.get_vertex_on_processor(x, y, p))
            results[core] = data_written

        return results

    def execute_application_data_specs(
            self, transceiver, machine, app_id, dsg_targets,
            uses_advanced_monitors, executable_targets, region_sizes,
            placements=None, extra_monitor_cores=None,
            extra_monitor_cores_to_ethernet_connection_map=None,
            report_folder=None, java_caller=None,
            processor_to_app_data_base_address=None,
            disable_advanced_monitor_usage=False):
        """ Execute the data specs for all non-system targets.

        :param ~spinn_machine.Machine machine:
            the python representation of the SpiNNaker machine
        :param ~spinnman.transceiver.Transceiver transceiver:
            the spinnman instance
        :param int app_id: the application ID of the simulation
        :param dict(tuple(int,int,int),int) region_sizes:
            the coord for region sizes for each core
        :param DataSpecificationTargets dsg_targets:
            map of placement to file path
        :param bool uses_advanced_monitors:
            whether to use fast data in protocol
        :param ~spinnman.model.ExecutableTargets executable_targets:
            what core will running what binary
        :param ~pacman.model.placements.Placements placements:
            where vertices are located
        :param list(ExtraMonitorSupportMachineVertex) extra_monitor_cores:
            the deployed extra monitors, if any
        :param extra_monitor_cores_to_ethernet_connection_map:
            how to talk to extra monitor cores
        :type extra_monitor_cores_to_ethernet_connection_map:
            dict(tuple(int,int), DataSpeedUpPacketGatherMachineVertex)
        :param processor_to_app_data_base_address:
            map of placement and DSG data
        :type processor_to_app_data_base_address:
            dict(tuple(int,int,int), DsWriteInfo)
        :param bool disable_advanced_monitor_usage:
            whether to avoid using advanced monitors even if they're available
        :return: map of placement and DSG data
        :rtype: dict(tuple(int,int,int),DataWritten) or DsWriteInfo
        """
        # pylint: disable=too-many-arguments
        if processor_to_app_data_base_address is None:
            processor_to_app_data_base_address = dict()
        self._write_info_map = processor_to_app_data_base_address
        self._db_folder = report_folder
        self._java = java_caller
        self._machine = machine
        self._txrx = transceiver
        self._app_id = app_id
        self._monitors = extra_monitor_cores
        self._placements = placements
        self._core_to_conn_map = extra_monitor_cores_to_ethernet_connection_map

        # Allow override to disable
        if disable_advanced_monitor_usage:
            uses_advanced_monitors = False

        impl_method = self.__java_app if java_caller else self.__python_app
        try:
            return impl_method(
                dsg_targets, executable_targets, uses_advanced_monitors,
                region_sizes)
        except:  # noqa: E722
            if uses_advanced_monitors:
                emergency_recover_states_from_failure(
                    self._txrx, self._app_id, executable_targets)
            raise

    def __set_router_timeouts(self):
        config = globals_variables.get_simulator().config
        n_channels = helpful_functions.read_config_int(
            config, "SpinnMan", "multi_packets_in_flight_n_channels")
        intermediate_channel_waits = helpful_functions.read_config_int(
            config, "SpinnMan", "multi_packets_in_flight_channel_waits")
        for receiver in itervalues(self._core_to_conn_map):
            receiver.load_system_routing_tables(
                self._txrx, self._monitors, self._placements)
            receiver.set_cores_for_data_streaming(
                self._txrx, self._monitors, self._placements,
                n_channels, intermediate_channel_waits)

    def __reset_router_timeouts(self):
        # reset router timeouts
        for receiver in itervalues(self._core_to_conn_map):
            receiver.unset_cores_for_data_streaming(
                self._txrx, self._monitors, self._placements)
            # reset router tables
            receiver.load_application_routing_tables(
                self._txrx, self._monitors, self._placements)

    def __select_writer(self, x, y):
        chip = self._machine.get_chip_at(x, y)
        ethernet_chip = self._machine.get_chip_at(
            chip.nearest_ethernet_x, chip.nearest_ethernet_y)
        gatherer = self._core_to_conn_map[ethernet_chip.x, ethernet_chip.y]
        return gatherer.send_data_into_spinnaker

    def __python_app(
            self, dsg_targets, executable_targets, use_monitors,
            region_sizes):
        """
        :param DataSpecificationTargets dsg_targets:
        :param ~spinnman.model.ExecutableTargets executable_targets:
        :param bool use_monitors:
        :param dict(tuple(int,int,int),int) region_sizes:
        :return: dict of cores to descriptions of what was written
        :rtype: dict(tuple(int,int,int),DataWritten)
        """
        dsg_targets = filter_out_system_executables(
            dsg_targets, executable_targets)

        if use_monitors:
            self.__set_router_timeouts()

        # create a progress bar for end users
        progress = ProgressBar(
            len(dsg_targets) * 2,
            "Executing data specifications and loading data for "
            "application vertices")

        # allocate and set user 0 before loading data
        base_addresses = dict()
        for core, _ in progress.over(
                iteritems(dsg_targets), finish_at_end=False):
            base_addresses[core] = self.__malloc_region_storage(
                core, region_sizes[core])

        total_sizes = defaultdict(int)
        matrix_sizes = defaultdict(int)
        connection_build_sizes = defaultdict(int)
        total_sizes_vertex = defaultdict(int)

        time = datetime.timedelta()
        for core, reader in progress.over(iteritems(dsg_targets)):
            x, y, p = core
            chip = self._machine.get_chip_at(x, y)
            data_written, matrix, connection, total, executor, time_taken = \
                self.__python_execute(
                    core, reader,
                    self.__select_writer(x, y)
                    if use_monitors else self._txrx.write_memory,
                    base_addresses[core], region_sizes[core],
                    self._placements.get_vertex_on_processor(x, y, p))
            self._write_info_map[core] = data_written
            time += time_taken

            vertex = self._placements.get_vertex_on_processor(x, y, p)

            for region_id in _MEM_REGIONS:
                region = executor.get_region(region_id)
                if region is not None:
                    total_sizes[(x, y, p, region_id)] = \
                        region.max_write_pointer
                    total_sizes_vertex[(vertex.label, region_id)] = \
                        region.max_write_pointer

            # write information for the memory map report
            total_sizes[(x, y, p, -1)] = total
            total_sizes[
                (0, chip.nearest_ethernet_x, chip.nearest_ethernet_y)] += total
            total_sizes[(-1, -1, -1, -1)] += total

            matrix_sizes[(x, y, p)] = matrix
            matrix_sizes[
                (0, chip.nearest_ethernet_x, chip.nearest_ethernet_y)] += \
                matrix
            matrix_sizes[(-1, -1, -1)] += matrix

            connection_build_sizes[(x, y, p)] = connection
            connection_build_sizes[
                (0, chip.nearest_ethernet_x, chip.nearest_ethernet_y)] += \
                connection
            connection_build_sizes[(-1, -1, -1)] += connection

        if use_monitors:
            self.__reset_router_timeouts()
        return (
            self._write_info_map, total_sizes, matrix_sizes,
            connection_build_sizes, time.total_seconds())

    def __java_app(
            self, dsg_targets, executable_targets, use_monitors,
            region_sizes):
        """
        :param DataSpecificationTargets dsg_targets:
        :param ~spinnman.model.ExecutableTargets executable_targets:
        :param bool use_monitors:
        :param dict(tuple(int,int,int),int) region_sizes:
        :return: map of cores to descriptions of what was written
        :rtype: DsWriteInfo
        """
        # create a progress bar for end users
        progress = ProgressBar(
            4, "Executing data specifications and loading data for "
            "application vertices using Java")

        dsg_targets.mark_system_cores(system_cores(executable_targets))
        progress.update()

        # Copy data from WriteMemoryIOData to database
        dw_write_info = self.__java_database(
            dsg_targets, progress, region_sizes)
        if use_monitors:
            self._java.set_placements(self._placements, self._txrx)

        self._java.execute_app_data_specification(use_monitors)

        progress.end()
        return (
            dw_write_info,
            {(-1, -1, -1, -1): dsg_targets.sum_over_region_sizes()},
             {(-1, -1, -1): 0}, {(-1, -1, -1): 0},
            dsg_targets.time_to_load_in_seconds())

    def execute_system_data_specs(
            self, transceiver, machine, app_id, dsg_targets, region_sizes,
            executable_targets, placements, report_folder=None,
            java_caller=None, processor_to_app_data_base_address=None):
        """ Execute the data specs for all system targets.

        :param ~spinnman.transceiver.Transceiver transceiver:
            the spinnman instance
        :param ~spinn_machine.Machine machine:
            the python representation of the spinnaker machine
        :param int app_id: the application ID of the simulation
        :param dict(tuple(int,int,int),str) dsg_targets:
            map of placement to file path
        :param dict(tuple(int,int,int),int) region_sizes:
            the coordinates for region sizes for each core
        :param ~spinnman.model.ExecutableTargets executable_targets:
            the map between binaries and locations and executable types
        :param str report_folder:
        :param JavaCaller java_caller:
        :param processor_to_app_data_base_address:
        :type processor_to_app_data_base_address:
            dict(tuple(int,int,int),DataWritten)
        :return: map of placement and DSG data, and loaded data flag.
        :rtype: dict(tuple(int,int,int),DataWritten) or DsWriteInfo
        """
        # pylint: disable=too-many-arguments

        if processor_to_app_data_base_address is None:
            processor_to_app_data_base_address = dict()
        self._write_info_map = processor_to_app_data_base_address
        self._machine = machine
        self._txrx = transceiver
        self._app_id = app_id
        self._db_folder = report_folder
        self._java = java_caller
        self._placements = placements

        impl_method = self.__java_sys if java_caller else self.__python_sys
        return impl_method(dsg_targets, executable_targets, region_sizes)

    def __java_sys(self, dsg_targets, executable_targets, region_sizes):
        """ Does the Data Specification Execution and loading using Java

        :param DataSpecificationTargets dsg_targets:
            map of placement to file path
        :param ~spinnman.model.ExecutableTargets executable_targets:
            the map between binaries and locations and executable types
        :param dict(tuple(int,int,int),int) region_sizes:
            the coord for region sizes for each core
        :return: map of cores to descriptions of what was written
        :rtype: DsWriteInfo
        """
        # create a progress bar for end users
        progress = ProgressBar(
            4, "Executing data specifications and loading data for system "
            "vertices using Java")

        dsg_targets.mark_system_cores(system_cores(executable_targets))
        progress.update()

        # Copy data from WriteMemoryIOData to database
        dw_write_info = self.__java_database(
            dsg_targets, progress, region_sizes)

        self._java.execute_system_data_specification()

        progress.end()
        return dw_write_info

    def __python_sys(self, dsg_targets, executable_targets, region_sizes):
        """ Does the Data Specification Execution and loading using Python

        :param DataSpecificationTargets dsg_targets:
            map of placement to file path
        :param ~spinnman.model.ExecutableTargets executable_targets:
            the map between binaries and locations and executable types
        :param dict(tuple(int,int,int),int) region_sizes:
            the coord for region sizes for each core
        :return: dict of cores to descriptions of what was written
        :rtype: dict(tuple(int,int,int),DataWritten)
        """
        # While the database supports having the info in it a python bugs does
        # not like iterating over and writing intermingled so using a dict
        sys_targets = filter_out_app_executables(
            dsg_targets, executable_targets)

        # create a progress bar for end users
        progress = ProgressBar(
            len(sys_targets) * 2,
            "Executing data specifications and loading data for "
            "system vertices")

        # allocate and set user 0 before loading data
        base_addresses = dict()
        for core, _ in progress.over(
                iteritems(sys_targets), finish_at_end=False):
            base_addresses[core] = self.__malloc_region_storage(
                core, region_sizes[core])

        for core, reader in progress.over(iteritems(sys_targets)):
            x, y, p = core
            data_written, _matrix, _connection, _total, _ex, _time = \
                self.__python_execute(
                    core, reader, self._txrx.write_memory, base_addresses[core],
                    region_sizes[core],
                    self._placements.get_vertex_on_processor(x, y, p))
            self._write_info_map[core] = data_written

        return self._write_info_map

    def __malloc_region_storage(self, core, size):
        """ Allocates the storage for all DSG regions on the core and tells \
            the core and our caller where that storage is.

        :param tuple(int,int,int) core: Which core we're talking about.
        :param int size:
            The total size of all storage for regions on that core, including
            for the header metadata.
        :return: address of region header table (not yet filled)
        :rtype: int
        """
        (x, y, p) = core

        # allocate memory where the app data is going to be written; this
        # raises an exception in case there is not enough SDRAM to allocate
        start_address = self._txrx.malloc_sdram(x, y, size, self._app_id)

        # set user 0 register appropriately to the application data
        write_address_to_user0(self._txrx, x, y, p, start_address)

        return start_address

    def __python_execute(
            self, core, reader, writer_func, base_address, size_allocated,
            machine_vertex):
        """
        :param tuple(int,int,int) core:
        :param ~.AbstractDataReader reader:
        :param callable(tuple(int,int,int,bytearray),None) writer_func:
        :param int base_address:
        :param int size_allocated:
        :param MachineVertex machine_vertex: the machine vertex
        :rtype: DataWritten
        """
        x, y, p = core
        total_size = 0

        # Maximum available memory.
        # However, system updates the memory available independently, so the
        # space available check actually happens when memory is allocated.
        memory_available = self._machine.get_chip_at(x, y).sdram.size

        # generate data spec executor
        executor = DataSpecificationExecutor(reader, memory_available)

        # run data spec executor
        try:
            executor.execute()
        except DataSpecificationException:
            logger.error("Error executing data specification for {}, {}, {}",
                         x, y, p)
            raise

        # Do the actual writing ------------------------------------

        # Write the header and pointer table
        header = executor.get_header()
        pointer_table = executor.get_pointer_table(base_address)
        data_to_write = numpy.concatenate((header, pointer_table)).tostring()

        # NB: DSE meta-block is always small (i.e., one SDP write)
        self._txrx.write_memory(x, y, base_address, data_to_write)
        bytes_written = len(data_to_write)

        matrix_size, connection_builder_size = self.__get_extra_sizes(
            machine_vertex, executor)

        for region_id in _MEM_REGIONS:
            region = executor.get_region(region_id)
            if region is not None:
                total_size += region.max_write_pointer

        time_total = datetime.timedelta()
        timer = Timer()
        # Write each region
        for region_id in _MEM_REGIONS:
            region = executor.get_region(region_id)
            if region is None:
                continue
            max_pointer = region.max_write_pointer
            if region.unfilled or max_pointer == 0:
                continue

            # Get the data up to what has been written
            data = region.region_data[:max_pointer]

            # Write the data to the position
            with timer:
                writer_func(x, y, pointer_table[region_id], data)
            time_total += timer.measured_interval

            bytes_written += len(data)

        return (
            DataWritten(base_address, size_allocated, bytes_written),
            matrix_size, connection_builder_size, total_size, executor,
            time_total)

    @staticmethod
    def __get_extra_sizes(machine_vertex, executor):
        matrix_size, connection_builder_size = 0, 0

        if isinstance(machine_vertex, PopulationMachineVertex):
            regions = POPULATION_BASED_REGIONS
            region = executor.get_region(regions.SYNAPTIC_MATRIX.value)  # 4
            matrix_size += region.max_write_pointer
            region = executor.get_region(regions.DIRECT_MATRIX.value)  # 10
            if region is not None:
                matrix_size += region.max_write_pointer
            region = executor.get_region(regions.CONNECTOR_BUILDER.value)  # 9
            if region is not None:
                connection_builder_size += region.max_write_pointer

        if isinstance(machine_vertex, DelayExtensionMachineVertex):
            regions = DelayExtensionMachineVertex.DELAY_EXTENSION_REGIONS
            region = executor.get_region(regions.DELAY_PARAMS.value)  # 1
            matrix_size += region.max_write_pointer
            region = executor.get_region(regions.EXPANDER_REGION.value)  # 3
            if region is not None:
                connection_builder_size += region.max_write_pointer

        return matrix_size, connection_builder_size
