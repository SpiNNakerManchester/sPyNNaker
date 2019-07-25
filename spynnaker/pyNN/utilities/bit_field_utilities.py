import math
from spinn_front_end_common.utilities.constants import WORD_TO_BYTE_MULTIPLIER
from pacman.utilities.algorithm_utilities. \
    partition_algorithm_utilities import determine_max_atoms_for_vertex
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.models.utility_models import DelayExtensionVertex

# number of elements
ELEMENTS_USED_IN_EACH_BIT_FIELD = 3  # n words, key, pointer to bitfield

ELEMENTS_USED_IN_BIT_FIELD_HEADER = 2  # n bitfields,  pointer for array

# n elements in each key to n atoms map for bitfield (key, n atoms)
N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP = 2

# the regions addresses needed (
#  pop table, synaptic matrix, direct matrix, bit_field, bit field builder,
# bit_field_key)
N_REGIONS_ADDRESSES = 5

# n key to n neurons maps size in words
N_KEYS_DATA_SET_IN_WORDS = 1

# the number of bits in a word (WHY IS THIS NOT A CONSTANT SOMEWHERE!)
BIT_IN_A_WORD = 32.0


def get_estimated_sdram_for_bit_field_region(app_graph, vertex):
    """ estimates the sdram for the bit field region
    :param app_graph: the app graph
    :param vertex: 
    :return: the estimated number of bytes used by the bit field region
    """
    sdram = 0
    for incoming_edge in app_graph.get_edges_ending_at_vertex(vertex):
        if isinstance(incoming_edge, ProjectionApplicationEdge):
            edge_pre_vertex = incoming_edge.pre_vertex
            max_atoms = determine_max_atoms_for_vertex(edge_pre_vertex)
            if incoming_edge.pre_vertex.n_atoms < max_atoms:
                max_atoms = incoming_edge.pre_vertex.n_atoms

            # Get the number of likely vertices
            n_machine_vertices = int(math.ceil(
                float(incoming_edge.pre_vertex.n_atoms) /
                float(max_atoms)))
            n_atoms_per_machine_vertex = int(math.ceil(
                float(incoming_edge.pre_vertex.n_atoms) /
                n_machine_vertices))
            if isinstance(edge_pre_vertex, DelayExtensionVertex):
                n_atoms_per_machine_vertex *= \
                    edge_pre_vertex.n_delay_stages
            n_words_for_atoms = int(math.ceil(
                n_atoms_per_machine_vertex / BIT_IN_A_WORD))
            sdram += (
                (ELEMENTS_USED_IN_EACH_BIT_FIELD + (
                    n_words_for_atoms * n_machine_vertices)) *
                WORD_TO_BYTE_MULTIPLIER)
    return sdram


def get_estimated_sdram_for_key_region(app_graph, vertex):
    """ gets an estimate of the bitfield builder region

    :param app_graph: the app graph
    :param vertex: 
    :return: sdram needed
    """

    # basic sdram
    sdram = N_KEYS_DATA_SET_IN_WORDS * WORD_TO_BYTE_MULTIPLIER
    for in_edge in app_graph.get_edges_ending_at_vertex(vertex):

        # Get the number of likely vertices
        edge_pre_vertex = in_edge.pre_vertex
        max_atoms = determine_max_atoms_for_vertex(edge_pre_vertex)
        if in_edge.pre_vertex.n_atoms < max_atoms:
            max_atoms = in_edge.pre_vertex.n_atoms
        n_edge_vertices = int(math.ceil(
            float(in_edge.pre_vertex.n_atoms) / float(max_atoms)))
        sdram += (n_edge_vertices * N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP *
                  WORD_TO_BYTE_MULTIPLIER)
    return sdram


def _exact_sdram_for_bit_field_region(
        machine_graph, vertex, n_key_map):
    """ calculates the correct sdram for the bitfield region based off \
        the machine graph and graph mapper

    :param machine_graph: machine graph
    :param vertex: the machine vertex
    :param n_key_map: n keys map
    :return: sdram in bytes
    """
    sdram = ELEMENTS_USED_IN_BIT_FIELD_HEADER * WORD_TO_BYTE_MULTIPLIER
    for incoming_edge in machine_graph.get_edges_ending_at_vertex(vertex):
        n_keys = n_key_map.n_keys_for_partition(
            machine_graph.get_outgoing_partition_for_edge(incoming_edge))
        n_words_for_atoms = int(math.ceil(n_keys / BIT_IN_A_WORD))

        sdram += (
            (ELEMENTS_USED_IN_EACH_BIT_FIELD + n_words_for_atoms) *
            WORD_TO_BYTE_MULTIPLIER)
    return sdram


def exact_sdram_for_bit_field_builder_region():
    """
    :return: 
    """
    return N_REGIONS_ADDRESSES * WORD_TO_BYTE_MULTIPLIER


def _exact_sdram_for_bit_field_key_region(machine_graph, vertex):
    return (
               N_KEYS_DATA_SET_IN_WORDS +
               len(machine_graph.get_edges_ending_at_vertex(vertex)) *
               N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP) * WORD_TO_BYTE_MULTIPLIER


def reserve_bit_field_regions(
        spec, machine_graph, n_key_map, vertex, bit_field_builder_region,
        bit_filter_region, bit_field_key_region):
    """

    :param spec: 
    :param machine_graph: 
    :param n_key_map: 
    :param vertex: 
    :param bit_field_builder_region: 
    :param bit_filter_region: 
    :param bit_field_key_region:
    :return: 
    """

    # reserve the final destination for the bitfields
    spec.reserve_memory_region(
        region=bit_filter_region,
        size=_exact_sdram_for_bit_field_region(
            machine_graph, vertex, n_key_map),
        label="bit_field region")

    # reserve region for the bitfield builder
    spec.reserve_memory_region(
        region=bit_field_builder_region,
        size=exact_sdram_for_bit_field_builder_region(),
        label="bit field builder region")

    # reserve memory region for the key region
    spec.reserve_memory_region(
        region=bit_field_key_region,
        size=_exact_sdram_for_bit_field_key_region(machine_graph, vertex),
        label="bit field key data")


def write_bitfield_init_data(
        spec, machine_vertex, machine_graph, routing_info, n_key_map,
        bit_field_builder_region, master_pop_region_id,
        synaptic_matrix_region_id, direct_matrix_region_id,
        bit_field_region_id, bit_field_key_map_region_id):
    """ writes the init data needed for the bitfield generator

    :param spec: data spec writer
    :param machine_vertex: machine vertex
    :param machine_graph: machine graph
    :param routing_info: keys
    :param n_key_map: map for edge to n keys
    :param bit_field_builder_region: the region id for the bitfield builder
    :param master_pop_region_id:
    :param synaptic_matrix_region_id:
    :param direct_matrix_region_id:
    :param bit_field_region_id:
    :param bit_field_key_map_region_id:
    :rtype: None
    """

    spec.switch_write_focus(bit_field_builder_region)

    spec.write_value(master_pop_region_id)
    spec.write_value(synaptic_matrix_region_id)
    spec.write_value(direct_matrix_region_id)
    spec.write_value(bit_field_region_id)
    spec.write_value(bit_field_key_map_region_id)

    spec.switch_write_focus(bit_field_key_map_region_id)

    # write n keys max atom map
    spec.write_value(
        len(machine_graph.get_edges_ending_at_vertex(machine_vertex)))

    # load in key to max atoms map
    for in_coming_edge in machine_graph.get_edges_ending_at_vertex(
            machine_vertex):
        out_going_partition = \
            machine_graph.get_outgoing_partition_for_edge(in_coming_edge)
        spec.write_value(
            routing_info.get_first_key_from_partition(out_going_partition))
        spec.write_value(
            n_key_map.n_keys_for_partition(out_going_partition))
