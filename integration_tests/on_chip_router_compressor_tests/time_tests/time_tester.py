from pacman.model.routing_tables.multicast_routing_table import \
    MulticastRoutingTable
from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables
from pacman.operations.router_compressors.mundys_router_compressor. \
    routing_table_condenser import MundyRouterCompressor
from spinn_front_end_common.interface.spinnaker_main_interface import \
    SpinnakerMainInterface

from spinn_front_end_common.mapping_algorithms. \
    on_chip_router_table_compression.mundy_on_chip_router_compression import \
    MundyOnChipRouterCompression
from spinn_front_end_common.utilities.utility_objs.executable_finder import \
    ExecutableFinder

from spinn_machine.multicast_routing_entry import MulticastRoutingEntry

from spynnaker.pyNN.utilities.conf import config

import random
import math
import time

n_entries = [100, 200, 400, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]

# set main interface
executable_finder = ExecutableFinder()
spinnaker = SpinnakerMainInterface(config, executable_finder)
spinnaker.set_up_machine_specifics(None)

# build transceiver and spinnaker machine
machine = spinnaker.machine
transceiver = spinnaker.transceiver
provenance_file_path = spinnaker._provenance_file_path
counter = 0

summary = ""

for n_entries_this_run in n_entries:
    transceiver.clear_multicast_routes(1, 1)
    routing_tables = MulticastRoutingTables()
    routing_table = MulticastRoutingTable(1, 1)
    random.seed(12345)

    # figure links
    links = set()
    n_links = random.randint(0, 5)
    for n_link in range(0, n_links):
        links.add(random.randint(0, 5))

    # figure processors
    processors = set()
    n_processors = random.randint(0, 15)
    for n_processor in range(0, n_processors):
        processors.add(random.randint(0, 15))

    defaultable = False
    if n_links == 1 and n_processors == 0:
        defaultable = bool(random.randint(0, 1))

    # build random entries
    while routing_table.number_of_entries < n_entries_this_run:

        # build entry
        multicast_routing_entry = MulticastRoutingEntry(
            routing_entry_key=random.randint(0, math.pow(2, 16)) << 16,
            defaultable=defaultable, mask=0xFFFF0000,
            link_ids=list(links), processor_ids=list(processors))

        # add router entry to router table
        if (routing_table.get_multicast_routing_entry_by_routing_entry_key(
                multicast_routing_entry.routing_entry_key,
                multicast_routing_entry.mask) is None):
            routing_table.add_mutlicast_routing_entry(
                multicast_routing_entry)

    # add to routing tables
    routing_tables.add_routing_table(routing_table)

    # build compressor
    mundy_compressor = MundyOnChipRouterCompression()

    # try running on chip compressor
    start_time = time.time()
    on_chip_failed = False
    try:
        mundy_compressor(
            routing_tables, transceiver, machine, 16, provenance_file_path,
            compress_only_when_needed=False, compress_as_much_as_possible=True)
    except Exception as e:
        print e
        on_chip_failed = True
    on_chip_time = time.time() - start_time

    # try running host compressor
    on_host_failed = False
    on_host = MundyRouterCompressor()
    start_time = time.time()
    try:
        on_host(routing_tables, target_length=None)
    except Exception as e:
        print e
        on_host_failed = True
    on_host_time = time.time() - start_time
    summary += "{:d}: host = {:f} chip = {:f}\n".format(
        n_entries_this_run, on_host_time, on_chip_time)
    print summary

    if on_chip_failed and on_host_failed:
        print "Stopping after {}".format(n_entries_this_run)
        break

transceiver.close()
