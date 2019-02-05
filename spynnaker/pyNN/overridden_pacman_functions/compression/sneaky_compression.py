from collections import defaultdict

import math

from pacman.model.routing_tables import UnCompressedMulticastRoutingTable
from pacman.model.routing_tables.compressed_multicast_routing_table import \
    CompressedMulticastRoutingTable
from spinn_machine import MulticastRoutingEntry


class SneakyCompression(object):

    __slots__ = [
        "_chip_cached_entries",
        "_threshold_packets"
    ]

    _BITS_IN_A_WORD = 32
    _MAX_SUPPORTED_LENGTH = 1023
    _BIT_MASK = 1

    # key id for the initial entry
    _ORIGINAL_ENTRY = 0

    # key id for the bitfield entries
    _ENTRIES = 1

    # mask for neuron level
    _NEURON_LEVEL_MASK = 0xFFFFFFFF

    def __init__(self, threshold_packets):
        self._threshold_packets = threshold_packets
        self._chip_cached_entries = defaultdict(dict)

    def compress(
            self, bit_fields_by_key, bit_fields_by_processor, routing_table,
            machine):
        """ attempt some skullduggery with routing tables

        :param routing_table: the entries to compress
        :param bit_fields_by_key: 
        :param bit_fields_by_processor: 
        :return: the compressed entries
        """

        max_packets_handleable = dict()
        for processor_id in bit_fields_by_processor.keys():
            packets_into_processor = 0
            for bf_data in bit_fields_by_processor[processor_id]:
                packets_into_processor += (
                    len(bf_data.bit_field) * self._BITS_IN_A_WORD)
            max_packets_handleable[processor_id] = packets_into_processor
            print "{}:{}".format(processor_id, packets_into_processor)

        # generate map between destinations and neurons
        basic_key_to_route_map = dict()
        for master_pop_key in bit_fields_by_key.keys():
            basic_key_to_route_map[master_pop_key] = \
                self._generate_map_between_routes_and_neurons(
                    bit_fields_by_key[master_pop_key],
                    routing_table.get_entry_by_routing_entry_key(
                        master_pop_key))

        # generate entries for these maps
        new_table = self._generate_sneaky_entries(
            basic_key_to_route_map, routing_table)

        total_entries = 0
        for key in new_table:
            total_entries += len(new_table[key])

        # check for the bitfields are ok.
        success = self.assess_bit_fields(
            total_entries, max_packets_handleable, new_table, bit_fields_by_key,
            routing_table, machine)

        # if going to fit and meet threshold
        if success:
            return new_table
        else:
            return self._search_for_mering_trickery(
                bit_fields_by_key, bit_fields_by_processor,
                basic_key_to_route_map, routing_table)

    def _search_for_mering_trickery(
            self, bit_fields_by_key, bit_fields_by_processor,
            basic_key_to_route_map, routing_table, reduction_costs_by_key):
        """
        
        :param bit_fields_by_key: 
        :param bit_fields_by_processor: 
        :param basic_key_to_route_map: 
        :param routing_table: 
        ;param reduction_costs_by_key:
        :return: 
        """
        total_entries = 0
        addable_keys = list()
        impact_keys = defaultdict(list)
        for master_pop_key in basic_key_to_route_map.keys():

            # get map from route to and neuron level
            (route_map, _) = basic_key_to_route_map[master_pop_key]

            # add to total entries knowing trickery (only cover neuron and a
            # overall for the rest)
            entries_for_key = 0
            for route_processors in route_map.keys():
                entries_for_key += len(route_map[route_processors])
                entries_for_key += 1

            if total_entries + entries_for_key < self._MAX_SUPPORTED_LENGTH:
                total_entries += entries_for_key
                addable_keys.append(master_pop_key)
            else:
                impact_keys[reduction_costs_by_key[master_pop_key]].append(
                    master_pop_key)

        # 



    def assess_bit_fields(
            self, total_entries, max_packets_handleable, entries,
            bit_fields_by_key, routing_table, machine):
        # if it'll fit into the router, see if the filtering reduces the
        # bandwidth to acceptable levels
        if total_entries < self._MAX_SUPPORTED_LENGTH:
            reduction_costs = self._deduce_reduction_costs(
                entries, bit_fields_by_key, routing_table, machine)
            for processor_id in max_packets_handleable.keys():
                if processor_id in reduction_costs:
                    new_cost = (
                        max_packets_handleable[processor_id] -
                        reduction_costs[processor_id])
                else:
                    new_cost = max_packets_handleable[processor_id]
                if new_cost > self._threshold_packets:
                    raise NotPassedThresholdException()
            return True
        else:
            return False

    def _deduce_reduction_costs(
            self, entries, bit_fields_by_key, routing_table, machine):
        # tally how many entries that would need and the reduction costs on a
        #  processor level
        reduction_costs = dict()

        n_processors_on_chip = machine.get_chip_at(
            routing_table.x, routing_table.y).n_processors

        for processor_id in range(0, n_processors_on_chip):
            reduction_costs[processor_id] = 0

        for original_entry in routing_table.multicast_routing_entries:
            n_neurons = bit_fields_by_key[original_entry.routing_entry_key]
            new_entries_to_key = entries[original_entry.routing_entry_key]



    def _generate_sneaky_entries(self, basic_key_to_route_map, routing_table):
        """ generate entries
        
        :param basic_key_to_route_map: key to route and neuron map
        :param routing_table: the original routing table
        :return: the compressed entries.
        """
        compressed_entries = defaultdict(list)

        # clone the original entries
        original_route_entries = list()
        original_route_entries.extend(routing_table.multicast_routing_entries)

        # go through the bitfields and get the routing table for it
        for key in basic_key_to_route_map.keys():
            bit_field_original_entry = \
                routing_table.get_entry_by_routing_entry_key(key)
            compressed_entries[key].extend(
                self._generate_entries_from_bitfield(
                    basic_key_to_route_map[key], bit_field_original_entry))
            # remove entry
            original_route_entries.remove(bit_field_original_entry)

        # add reduced to front of the tables
        for entry in original_route_entries:
            compressed_entries[entry.routing_entry_key] = entry
        return compressed_entries

    def _generate_entries_from_bitfield(
            self, neuron_level_entries_by_route, original_entry):
        """ trickery for generating bitfields
        
        :param neuron_level_entries_by_route: 
        :param original_entry: 
        :return: compressed entries
        """
        entries = list()

        for processors in neuron_level_entries_by_route.keys():
            sets_of_next_to_neurons = \
                self._locate_seq(neuron_level_entries_by_route[processors])
            for group in sets_of_next_to_neurons:
                entries.extend(self._process_a_group(
                    original_entry, group, processors))

        # add overarching entry to kill all packets to cores on chip as needed
        #entries.append(MulticastRoutingEntry(
        #    routing_entry_key=original_entry.routing_entry_key,
        #    mask=original_entry.mask, processor_ids=[],
        #    link_ids=original_entry.link_ids, defaultable=False))
        return entries

    def _process_a_group(self, original_entry, group, processors):
        if len(group) == 0:
            return []
        if len(group) == 1:
            return [MulticastRoutingEntry(
                routing_entry_key=original_entry.routing_entry_key + group[0],
                mask=self._NEURON_LEVEL_MASK, processor_ids=processors,
                link_ids=original_entry.link_ids, defaultable=False)]
        else:
            entries = list()

            # if the first entry in the group has a 1 at the low end,
            # treat it separately
            if group[0] & 1 == 1:
                entries.append(
                    MulticastRoutingEntry(
                        routing_entry_key=original_entry.routing_entry_key +
                                          group[0],
                        mask=self._NEURON_LEVEL_MASK, processor_ids=processors,
                        link_ids=original_entry.link_ids, defaultable=False))
                group.remove(group[0])

            bits_covered = int(math.floor(math.log(len(group), 2)))
            modified_mask = (
                (self._NEURON_LEVEL_MASK << bits_covered) &
                self._NEURON_LEVEL_MASK)
            entries.append(MulticastRoutingEntry(
                routing_entry_key=original_entry.routing_entry_key + group[0],
                mask=modified_mask, processor_ids=processors,
                link_ids=original_entry.link_ids, defaultable=False))

            entries.extend(self._process_a_group(
                original_entry, group[int(math.pow(2, bits_covered)):],
                processors))
            return entries

    @staticmethod
    def _locate_seq(neurons):
        neurons.sort()
        groups = list()
        current_track = list()
        neuron_tracking = neurons[0] - 1
        for neuron in neurons:
            if neuron_tracking + 1 == neuron:
                current_track.append(neuron)
                neuron_tracking += 1
            else:
                neuron_tracking = neuron
                groups.append(current_track)
                current_track = list()
                current_track.append(neuron)
        groups.append(current_track)
        return groups

    def _generate_map_between_routes_and_neurons(
            self, bit_fields, routing_table_entry, key_to_n_atoms_map):
        """ sneaky router entries which are kinda compressed
        :param bit_fields: the bitfields for a given key
        :param routing_table_entry: the original entry from it
        :return: entries in a ordered sneaky way
        """

        n_neurons = key_to_n_atoms_map[routing_table_entry.routing_entry_key]

        # processors to consider here
        processors_filtered = list()
        for bf_data in bit_fields:
            processors_filtered.append(bf_data.processor_id)

        neuron_level_entries_by_route = defaultdict(list)

        # check each neuron to see if any bitfields care, and if so,
        # add processor
        for neuron in range(0, n_neurons):
            processors = list()

            # add processors that are not going to be filtered
            for processor_id in routing_table_entry.processor_ids:
                if processor_id not in processors_filtered:
                    processors.append(processor_id)

            # process bitfields
            for bf_data in bit_fields:
                if self._bit_for_neuron_id(bf_data.bit_field, neuron):
                    processors.append(bf_data.processor_id)

            # build new entry for this neuron
            neuron_level_entries_by_route[frozenset(processors)].append(neuron)
        return neuron_level_entries_by_route

    def _bit_for_neuron_id(self, bit_field, neuron_id):
        """ locate the bit for the neuron in the bitfield

        :param bit_field: the block of words which represent the bitfield
        :param neuron_id: the neuron id to find the bit in the bitfield
        :return: the bit
        """
        word_id = int(math.floor(neuron_id // self._BITS_IN_A_WORD))
        bit_in_word = neuron_id % self._BITS_IN_A_WORD
        flag = (bit_field[word_id] >> bit_in_word) & self._BIT_MASK
        return flag


class NotPassedThresholdException(Exception):
    """ the exception that says that it did fit into the router table, 
    but with the likely hood of overloaded cores.
    """

    def __init__(self):
        pass
