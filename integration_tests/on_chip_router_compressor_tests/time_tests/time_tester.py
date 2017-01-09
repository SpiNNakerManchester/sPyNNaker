import os
from rig.routing_table import MinimisationFailedError
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
from spinn_front_end_common.utilities.exceptions import SpinnFrontEndException
from spinn_front_end_common.utilities.utility_objs.executable_finder import \
    ExecutableFinder

from spinn_machine.multicast_routing_entry import MulticastRoutingEntry

from spynnaker.pyNN.utilities.conf import config

import random
import math
import time

n_entries = [100, 200, 400, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
time_frame = dict()
time_frame_host = dict()

# set main interface
executable_finder = ExecutableFinder()
spinnaker = SpinnakerMainInterface(config, executable_finder)
spinnaker.set_up_machine_specifics(None)

# build transceiver and spinnaker machine
machine = spinnaker.machine
transceiver = spinnaker.transceiver
provenance_file_path = spinnaker._provenance_file_path

for n_entries_this_run in n_entries:
    routing_tables = MulticastRoutingTables()
    routing_table = MulticastRoutingTable(1, 1)
    random.seed(12345)

    # build 4000 random entries
    for entry in range(0, n_entries_this_run):

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

        # build entry
        multicast_routing_entry = MulticastRoutingEntry(
            routing_entry_key=random.randint(0, math.pow(2, 32)),
            defaultable=defaultable, mask=0xFFFFFFFF,
            link_ids=list(links), processor_ids=list(processors))

        # add router entry to router table
        routing_table.add_mutlicast_routing_entry(
            multicast_routing_entry)

    # add to routing tables
    routing_tables.add_routing_table(routing_table)

    # build compressor
    mundy_compressor = MundyOnChipRouterCompression()

    # try running on chip compressor
    try:
        _, prov_items = mundy_compressor(
            routing_tables, transceiver, machine, 16, 16, provenance_file_path)
        time_frame[n_entries_this_run] = prov_items[0].message
    except SpinnFrontEndException as e:
        reader = open(os.path.join(
            provenance_file_path,
            "on_chip_routing_table_compressor_run_time.xml"))
        reader.readline()
        data = reader.readline()
        bits = data.split(">")
        time_frame[n_entries_this_run] = float(bits[1])

    # try running host compressor
    on_host = MundyRouterCompressor()
    start_time = time.time()
    try:
        on_host(routing_tables)
        end_time = time.time()
        time_frame_host[n_entries_this_run] = end_time - start_time
    except MinimisationFailedError:
        end_time = time.time()
        time_frame_host[n_entries_this_run] = end_time - start_time

# print entries to the terminal for recording
for entry in n_entries:
    print "host = [{}]      chip = [{}] \n".format(time_frame_host[entry],
                                                   time_frame[entry])
