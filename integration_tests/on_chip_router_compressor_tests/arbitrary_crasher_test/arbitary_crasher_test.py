from pacman.model.routing_tables.multicast_routing_table import \
    MulticastRoutingTable
from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables
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

routing_tables = MulticastRoutingTables()
routing_table = MulticastRoutingTable(1, 1)
random.seed(12345)

# build 4000 random entries
for entry in range(0, 1500):

    # figure links
    links = set()
    n_links = random.randint(0, 5)
    for n_link in range(0, n_links):
        links.add(random.randint(0, 5))

    defaultable = False
    if n_links == 1:
        defaultable = bool(random.randint(0, 1))

    # figure processors
    processors = set()
    n_processors = random.randint(0, 16)
    for n_processor in range(0, n_processors):
        processors.add(random.randint(0, 16))

    # build entry
    multicast_routing_entry = MulticastRoutingEntry(
        routing_entry_key=random.randint(0, math.pow(2, 32)),
        defaultable=defaultable,
        mask=0xFFFFFFFF,
        link_ids=list(links),
        processor_ids=list(processors))

    # add router entry to router table
    routing_table.add_mutlicast_routing_entry(
        multicast_routing_entry)

# add to routing tables
routing_tables.add_routing_table(routing_table)

# build compressor
mundy_compressor = MundyOnChipRouterCompression()

# set main interface
executable_finder = ExecutableFinder()
spinnaker = SpinnakerMainInterface(config, executable_finder)
spinnaker.set_up_machine_specifics(None)

# build transceiver and spinnaker machine
machine = spinnaker.machine
transceiver = spinnaker.transceiver
provenance_file_path = spinnaker._provenance_file_path

# try running compressor
try:
    mundy_compressor(
        routing_tables, transceiver, machine, 16, provenance_file_path)
    raise Exception("Compressor should have crashed but didn't")
except SpinnFrontEndException as e:
    print "passed test"
    pass
