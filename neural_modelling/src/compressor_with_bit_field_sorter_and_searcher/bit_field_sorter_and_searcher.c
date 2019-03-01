#include <spin1_api.h>
#include <debug.h>
#include <bit_field.h>
#include <sdp_no_scp.h>
#include "common-typedefs.h"
#include "../common/compressor_common/platform.h"
#include "../common/compressor_common/routing_table.h"
#include "../common/compressor_common/compression_sdp_formats.h"
#include "../common/compressor_common/constants.h"
/*****************************************************************************/
/* SpiNNaker routing table minimisation with bitfield integration control core.
 *
 * controls the attempt to minimise the router entries with bitfield
 * components.
 */

typedef struct comp_core_store{
    // how many
    uint32_t n_elements;
    // compressed table location
    address_t compressed_table;
    // elements
    address_t * elements;
} comp_core_store;

//! \brief struct for bitfield by processor
typedef struct _bit_field_by_processor_t{
    // processor id
    uint32_t processor_id;
    // length of list
    uint32_t length_of_list;
    // list of addresses where the bitfields start
    address_t* bit_field_addresses;
} _bit_field_by_processor_t;

//! \brief struct for processor coverage by bitfield
typedef struct _proc_cov_by_bitfield_t{
    // processor id
    uint32_t processor_id;
    // length of the list
    uint32_t length_of_list;
    // list of the number of redundant packets from a bitfield
    uint32_t* redundant_packets;
} _proc_cov_by_bitfield_t;

//! \brief struct for n redundant packets and the bitfield addresses of it
typedef struct _coverage{
    // n redundant packets
    uint n_redundant_packets;
    // length of list
    uint32_t length_of_list;
    // list of corresponding processor id to the bitfield addresses list
    uint32_t* processor_ids;
    // list of addresses of bitfields with this x redundant packets
    address_t* bit_field_addresses;
} _coverage;

//! \brief struct holding keys and n bitfields with key
typedef struct _master_pop_bit_field{
    // the master pop key
    uint32_t master_pop_key;
    // the number of bitfields with this key
    uint32_t n_bitfields_with_key;
} _master_pop_bit_field;

//=============================================================================

//! enum for the different states to report through the user2 address.
typedef enum exit_states_for_user_one{
    EXITED_CLEANLY = 0, EXIT_FAIL = 1, EXIT_MALLOC = 2
} exit_states_for_user_two;

//! enum mapping for elements in uncompressed routing table region
typedef enum uncompressed_routing_table_region_elements{
    APPLICATION_APP_ID = 0, N_ENTRIES = 1, START_OF_UNCOMPRESSED_ENTRIES = 2
} uncompressed_routing_table_region_elements;

//! enum for the compressor cores data elements (used for programmer debug)
typedef enum compressor_core_elements{
    N_COMPRESSOR_CORES = 0, START_OF_comp_core_idS = 1
} compressor_core_elements;

//! enum mapping user register to data that's in there (only used by
//! programmer for documentation)
typedef enum user_register_maps{
    APPLICATION_POINTER_TABLE = 0, UNCOMP_ROUTER_TABLE = 1,
    REGION_ADDRESSES = 2, USABLE_SDRAM_REGIONS = 3,
    USER_REGISTER_LENGTH = 4
} user_register_maps;

//! enum mapping of elements in the key to atom mapping
typedef enum key_to_atom_map_elements{
    SRC_BASE_KEY = 0, SRC_N_ATOMS = 1, LENGTH_OF_KEY_ATOM_PAIR = 2
} key_to_atom_map_elements;

//! enum mapping addresses in addresses region
typedef enum addresses_elements{
    BITFIELD_REGION = 0, KEY_TO_ATOM_REGION = 1, PROCESSOR_ID = 2,
    ADDRESS_PAIR_LENGTH = 3
} addresses_elements;

//! enum mapping bitfield region top elements
typedef enum bit_field_data_top_elements{
    N_BIT_FIELDS = 0, START_OF_BIT_FIELD_TOP_DATA = 1
} bit_field_data_top_elements;

//! enum mapping top elements of the addresses space
typedef enum top_level_addresses_space_elements{
    N_PAIRS = 0, START_OF_ADDRESSES_DATA = 1
} top_level_addresses_space_elements;

//! enum stating the components of a bitfield struct
typedef enum bit_field_data_elements{
    BIT_FIELD_BASE_KEY = 0, BIT_FIELD_N_WORDS = 1, START_OF_BIT_FIELD_DATA = 2
} bit_field_data_elements;

//! callback priorities
typedef enum priorities{
    COMPRESSION_START_PRIORITY = 3, SDP_PRIORITY = -1
}priorities;

//============================================================================

//! flag for saying compression core doing nowt
#define DOING_NOWT -1

//! bits in a word
#define BITS_IN_A_WORD 32

//! bit shift for the app id for the route
#define ROUTE_APP_ID_BIT_SHIFT 24

//! max number of processors on chip used for app purposes
#define MAX_PROCESSORS 18

//! max number of links on a router
#define MAX_LINKS_PER_ROUTER 6

//! size of x routing entries in bytes
#define X_ROUTING_TABLE_ENTRIES_SDRAM_SIZE 4

//! neuron level mask
#define _NEURON_LEVEL_MASK 0xFFFFFFFF

//! how many tables the uncompressed router table entries is
#define N_UNCOMPRESSED_TABLE 1

//============================================================================

//! time to take per compression iteration
uint32_t time_per_iteration = 0;

//! flag of how many times the timer has fired during this one
uint32_t finish_compression_flag = 0;

//! easier programming tracking of the user registers
address_t user_register_content[USER_REGISTER_LENGTH];

//! best routing table position in the search
uint32_t best_search_point = 0;

//! the last routing table position in the search
uint32_t last_search_point = 0;

//! the store for the last routing table that was compressed
table_t last_compressed_table;

//! the compressor app id
uint32_t app_id = 0;

// how many bitfields there are
uint n_bf_addresses = 0;

//! how many entries are in the uncompressed version
uint32_t total_entries_in_uncompressed_router_table = 0;

//! the list of bitfields in sorted order based off best effect.
address_t * sorted_bit_fields;

//! the list of the addresses of the routing table entries for the bitfields 
//! and reduced routing table
address_t * bit_field_routing_tables;

// the list of compressor cores to bitfield routing table sdram addresses
comp_core_store ** comp_cores_bf_tables;

//! list of bitfield associated processor ids. sorted order based off best
//! effort linked to sorted_bit_fields, but separate to avoid sdram rewrites
uint32_t * sorted_bit_fields_processor_ids;

//! list of processor ids which will be running the compressor binary
uint32_t * compressor_cores;

//! how many compression cores there are
uint32_t n_compression_cores;

//! how many compression cores are available
uint32_t n_available_compression_cores;

//! stores which values have been tested
bit_field_t tested_mid_points;

//! stores which mid points have successes or failed
bit_field_t mid_points_successes;

//! tracker for what each compressor core is doing (in terms of midpoints)
int * c_core_mid_point;

//! the bitfield by processor global holder
_bit_field_by_processor_t* bit_field_by_processor;

//! the current length of the filled sorted bit field.
uint32_t sorted_bit_field_current_fill_loc = 0;

//! \brief sdp message to send control messages to compressors cores
sdp_msg_pure_data my_msg;

//============================================================================

//! \brief sends the sdp message. assumes all params have already been set
void send_sdp_message(){
    log_info("sending message");
    while (!spin1_send_sdp_msg((sdp_msg_t *) &my_msg, _SDP_TIMEOUT)) {
        // Empty body
    }
    log_info("sent message");
}

//! \brief sends a sdp message forcing the processor to stop its compression
//! attempt
//! \param[in] processor_id: the processor to force stop compression attempt
//! \return bool saying successfully sent the message
void send_sdp_force_stop_message(uint32_t processor_id){
    // set message params
    my_msg.dest_port = (RANDOM_PORT << PORT_SHIFT) | processor_id;
    my_msg.data[COMMAND_CODE] = STOP_COMPRESSION_ATTEMPT;
    my_msg.length = LENGTH_OF_SDP_HEADER + COMMAND_CODE_SIZE_IN_BYTES;
    
    // send sdp packet
    send_sdp_message();
}

//! \brief sets up the search bitfields.
//! \return bool saying success or failure of the setup
bool set_up_search_bitfields(){
    tested_mid_points = bit_field_alloc(n_bf_addresses);
    mid_points_successes = bit_field_alloc(n_bf_addresses);

    // check the malloc worked
    if (tested_mid_points == NULL){
        return false;
    }
    if (mid_points_successes == NULL){
        FREE(tested_mid_points);
        return false;
    }

    // return if successful
    return true;
}

//! \brief gets data about the bitfields being considered
//! \param[in/out] keys: the data holder to populate
//! \param[in] mid_point: the point in the sorted bit fields to look for
//! \return the number of unique keys founds.
uint32_t population_master_pop_bit_fields(
        _master_pop_bit_field * keys, uint32_t mid_point){

    uint32_t n_keys = 1;
    // how many in each key
    for (uint32_t bit_field_index = 0; bit_field_index < mid_point;
            bit_field_index++){
        uint32_t key = sorted_bit_fields[bit_field_index][BIT_FIELD_BASE_KEY];
        uint32_t keys_index = 0;
        bool found = false;
        while(!found || keys_index < n_keys){
            if (keys[keys_index].master_pop_key == key){
                found = true;
                keys[keys_index].n_bitfields_with_key ++;
            }
            keys_index ++;
        }
        if (!found){
            keys[n_keys].master_pop_key = key;
            keys[n_keys].n_bitfields_with_key = 1;
            n_keys ++;
        }
    }
    return n_keys;
}

//! locates a entry within a routing table, extracts the data, then removes
//! it from the table, updating locations and sizes
//! \param[in] uncompressed_table_address:
//! \param[in] master_pop_key: the key to locate the entry for
//! \param[in/out] entry_to_store: entry to store the found entry in
//! \return: None
void extract_and_remove_entry_from_table(
        address_t uncompressed_table_address, uint32_t master_pop_key,
        entry_t* entry_to_store){

    // cas the address to the struct for easier work
    table_t* table_cast = (table_t*) &uncompressed_table_address;

    // flag for when found. no point starting move till after
    bool found = false;

    // iterate through all entries
    for(uint32_t entry_id=0; entry_id < table_cast->size; entry_id++){

        // if key mathces, sotre entry (assumes only 1 entry, otherwise boomed)
        if (table_cast->entries[entry_id].key_mask.key == master_pop_key){
            entry_to_store->route = table_cast->entries[entry_id].route;
            entry_to_store->source = table_cast->entries[entry_id].source;
            entry_to_store->key_mask.key =
                table_cast->entries[entry_id].key_mask.key;
            entry_to_store->key_mask.mask =
                table_cast->entries[entry_id].key_mask.mask;
            found = true;
        }
        else{  // not found entry here. check if already found
            if (found){  // if found, move entry up one. to sort out memory
                table_cast->entries[entry_id - 1]->route =
                    table_cast->entries[entry_id].route;
                table_cast->entries[entry_id - 1]->source =
                    table_cast->entries[entry_id].source;
                table_cast->entries[entry_id - 1]->key_mask.key =
                    table_cast->entries[entry_id].key_mask.key;
                table_cast->entries[entry_id - 1]->key_mask.mask =
                    table_cast->entries[entry_id].key_mask.mask;
            }
        }
    }

    // update size by the removal of 1 entry
    table_cast->size -= 1;
}

//! \brief finds the processor id of a given bitfield address (search though
//! the bit field by processor
//! \param
uint32_t locate_processor_id_from_bit_field_address(
        address_t bit_field_address){

    uint32_t n_pairs = user_register_content[REGION_ADDRESSES][N_PAIRS];
    for(uint32_t bf_by_proc = 0; bf_by_proc < n_pairs; bf_by_proc++){

    }
    bit_field_by_processor
}

bool generate_entries_from_bitfields(
        address_t* addresses, uint32_t n_bit_fields, entry_t original_entry,
        address_t* rt_address){
    uint32_t size = get_bit_field_size(MAX_PROCESSORS + MAX_LINKS_PER_ROUTER);

    bit_field_t processors =
        bit_field_alloc(MAX_PROCESSORS + MAX_LINKS_PER_ROUTER);
    clear_bit_field(processors, size);

    if (processors == NULL){
        log_error(
            "could not allocate memory for the processor tracker when "
            "making entries from bitfields");
        return false;
    }

    // cast original entry route to a bitfield for ease of use
    bit_field* original_route = (bit_field_t) &original_entry.route;

    for (uint32_t processor_id = 0; processor_id < MAX_PROCESSORS;
            processor_id++){
        if (bit_field_test(
                original_route, processor_id + MAX_LINKS_PER_ROUTER)){
            bool found = false;
            for (uint32_t bit_field_index = 0; bit_field_index < n_bit_fields;
                    bit_field_index++){
                if(addresses[bit_field_index][])
            }
        }
    }



}

//! generates the routing table entries from this set of bitfields
//! \param[in] master_pop_key: the key to locate the bitfields for
//! \param[in] uncompressed_table: the location for the uncompressed table
//! \param[in] n_bit_fields: how many bitfields are needed for this key
//! \param[in] mid_point: the point where the search though sorted bit fields
//! ends.
//! \param[in] rt_address: the location in sdram to store the routing table
//! generated from the bitfields and original entry.
//! \return bool saying if it was successful or not
bool generate_rt_from_bit_field(
        uint32_t master_pop_key, address_t uncompressed_table,
        uint32_t n_bit_fields, uint32_t mid_point, address_t* rt_address){

    // reduce future iterations, by finding the exact bitfield addresses
    address_t* addresses = MALLOC(n_bit_fields * sizeof(address_t));
    uint32_t index = 0;
    for (uint32_t bit_field_index = 0; bit_field_index < mid_point;
            bit_field_index++){
        if (sorted_bit_fields[bit_field_index][BIT_FIELD_BASE_KEY] ==
                master_pop_key){
            addresses[index] = sorted_bit_fields[bit_field_index];
        }
    }

    // extract original routing entry from uncompressed table
    entry_t original_entry;
    extract_and_remove_entry_from_table(uncompressed_table, master_pop_key);

    // create table entries with bitfields
    bool success = generate_entries_from_bitfields(
        addresses, n_bit_fields, original_entry, rt_address);
    if (!success){
        log_error(
            "can not create entries for key %d with %x bitfields.",
            master_pop_key, n_bit_fields);
        FREE(addresses);
        return false;
    }

    FREE(addresses);
    return true;
}

//! \brief clones the un compressed routing table, to another sdram location
//! \param[in/out] where_was_cloned: the address where the cloned table is
//! located.
//! \return: bool saying if the cloning was successful or not
bool clone_un_compressed_routing_table(address_t* where_was_cloned){
    uint32_t x_entries = user_register_content[UNCOMP_ROUTER_TABLE][N_ENTRIES];
    uint32_t sdram_used = (X_ROUTING_TABLE_ENTRIES_SDRAM_SIZE + (
        x_entries * sizeof(entry_t) * WORD_TO_BYTE_MULTIPLIER));

    // allocate sdram for the clone
    address_t sdram_clone_of_routing_table = MALLOC_SDRAM(sdram_used);
    if (sdram_clone_of_routing_table == NULL){
        log_error("failed to allocate sdram for the cloned routing table for "
                  "uncompressed compression attempt");
        return false;
    }

    // copy over data
    sark_mem_cpy(
        sdram_clone_of_routing_table,
        &user_register_content[UNCOMP_ROUTER_TABLE][N_ENTRIES],
        sdram_used);
    return true;
}

//! takes a midpoint and reads the sorted bitfields up to that point generating
//! bitfield routing tables and loading them into sdram for transfer to a
//! compressor core
//! \param[in] mid_point: where in the sorted bitfields to go to
//! \param[out] n_rt_addresses: how many addresses are needed for the
//! tables
//! \return bool saying if it successfully built them into sdram
bool create_bit_field_router_tables(
        uint32_t mid_point, uint32_t* n_rt_addresses){
    // sort out bitfields by key

    // get n keys that exist
    _master_pop_bit_field * keys = MALLOC(
        mid_point * sizeof(_master_pop_bit_field));
    if (keys == NULL){
        log_error("cannot allocate memory for keys");
        return false;
    }

    // populate the master pop bit field
    n_rt_addresses = population_master_pop_bit_fields(keys, mid_point);

    // add the uncompressed table, for allowing the bitfield table generator to
    // edit accordingly.
    n_rt_addresses += 1;
    address_t* uncompressed_table;
    bool suc = clone_un_compressed_routing_table(uncompressed_table);
    if (!suc){
        log_error(
            "failed to clone uncompressed tables for attempt %d", mid_point);
        FREE(keys);
        return false;
    }

    // add clone to front of list, to ensure its easily accessible (plus its
    // part of the expected logic)
    bit_field_routing_tables[0] = uncompressed_table;

    bit_field_routing_tables = MALLOC(n_rt_addresses * sizeof(address_t));
    if (bit_field_routing_tables == NULL){
        log_info("failed to allocate memory for bitfield routing tables");
        FREE(keys);
        return false;
    }

    // iterate through the keys, accumulating bitfields and turn into routing
    // table entries.
    for(uint32_t key_index = 1; keys_index < n_rt_addresses; key_index++){
        address_t* rt_address;
        bool success = generate_rt_from_bit_field(
            keys[key_index -1]->master_pop_key, uncompressed_table,
            keys[key_index - 1]->n_bitfields_with_key, mid_point, rt_address);

        // if failed, free stuff and tell above it failed
        if (!success){
            log_info("failed to allocate memory for rt table");
            FREE(keys);
            FREE(bit_field_routing_tables);
            return false;
        }

        // store the rt address for this master pop key
        bit_field_routing_tables[key_index] = rt_address
    }
    return true;
}

//! \brief selects a compression core that's not doing anything yet
//! \param[in] midpoint: the midpoint this compressor is going to explore
//! \return the compressor core id for this attempt.
uint32_t select_compressor_core(uint32_t midpoint){
    for(uint32_t comp_core_index = 0; comp_core_index < n_compression_cores;
            comp_core_index++){
        if (c_core_mid_point[comp_core_index] == DOING_NOWT){
            c_core_mid_point[comp_core_index] = midpoint;
            n_available_compression_cores -= 1;
            return compressor_cores[comp_core_index];
        }
    }
    log_error("cant find a core to allocate to you");
    rt_error(RTE_SWERR);
    return 0;  // needed for compiler warning to shut up
}

//! \brief stores the addresses for freeing when response code is sent
//! \param[in] n_rt_addresses: how many bit field addresses there are
//! \param[in] comp_core_id: the compressor core
//! \param[in] compressed_address: the addresses for the compressed routing
//! table
//! \return bool stating if stored or not
bool record_address_data_for_response_functionality(
        uint32_t n_rt_addresses, uint32_t comp_core_id,
        address_t compressed_address){

    // allocate memory for storing tracker for the response process
    comp_cores_bf_tables[comp_core_id] = MALLOC(sizeof(comp_core_store));
    if (comp_cores_bf_tables[comp_core_id] == NULL){
        log_error("cannot allocate memory for sdram tracker");
        return false;
    }

    // allocate memory for the elements
    comp_cores_bf_tables[comp_core_id]->elements = MALLOC(
        n_rt_addresses * sizeof(address_t));
    if (comp_cores_bf_tables[comp_core_id]->elements == NULL){
        log_error("cannot allocate memory for sdram tracker of addresses");
        return false;
    }

    // store the elements. note need to copy over, as this is a central malloc
    // space for the routing tables.
    comp_cores_bf_tables[comp_core_id]->n_elements = n_rt_addresses;
    comp_cores_bf_tables[comp_core_id]->compressed_table = compressed_address;
    comp_cores_bf_tables[comp_core_id]->elements = &bit_field_routing_tables;
    return true;
}


//! \brief update the mc message to point at right direction
//! \param[in] comp_core_id: the compressor core id.
void update_mc_message(uint32_t comp_core_id){
    log_info("chip id = %d", spin1_get_chip_id());
    my_msg.srce_addr = spin1_get_chip_id();
    my_msg.dest_addr = spin1_get_chip_id();
    my_msg.flags = REPLY_NOT_EXPECTED;
    log_info("core id =  %d", spin1_get_id());
    my_msg.srce_port = (RANDOM_PORT << PORT_SHIFT) | spin1_get_core_id();
    log_info("compressor core = %d", comp_core_id);
    my_msg.dest_port = (RANDOM_PORT << PORT_SHIFT) | comp_core_id;
}

//! \brief figure out how many packets are needed to transfer the addresses over
//! \param[in] n_rt_addresses: how many addresses to send
//! \return the number of packets needed
uint32_t deduce_total_packets(uint32_t n_rt_addresses){
    uint32_t total_packets = 1;
    uint32_t n_addresses_for_start =
        ITEMS_PER_DATA_PACKET - sizeof(start_stream_sdp_packet_t);
    if (n_addresses_for_start < n_rt_addresses){
        n_rt_addresses -= n_addresses_for_start;
        total_packets += n_rt_addresses / (
            ITEMS_PER_DATA_PACKET - sizeof(extra_stream_sdp_packet_t));
        uint32_t left_over = n_rt_addresses % (
            ITEMS_PER_DATA_PACKET - sizeof(extra_stream_sdp_packet_t));
        if (left_over != 0){
            total_packets += 1;
        }
    }
    log_info("n packets = %d", total_packets);
    return total_packets;
}

//! \brief deduce n elements in this packet
//! \param[in] packet_id: the packet id to consider
//! \param[in] n_rt_addresses: how many bit field packets there are left
//! to send.
//! \param[in] addresses_sent: the amount of addresses already sent by other
//! sdp messages
//! \return: the number of addresses in this packet.
uint32_t deduce_elements_this_packet(
        uint32_t packet_id, uint32_t n_rt_addresses, uint32_t addresses_sent){
    uint32_t n_addresses_this_message = 0;
    uint32_t size_first =
        ITEMS_PER_DATA_PACKET - sizeof(start_stream_sdp_packet_t);
    uint32_t size_extra =
        ITEMS_PER_DATA_PACKET - sizeof(extra_stream_sdp_packet_t);

    // if first packet
    if (packet_id == 0){
        if ((n_rt_addresses - addresses_sent) <= size_first){
            n_addresses_this_message = n_rt_addresses - addresses_sent;
        }
        else{
            n_addresses_this_message = size_first;
        }
    }
    // else a extra packet
    else{
        if ((n_rt_addresses - addresses_sent) < size_extra){
            n_addresses_this_message = n_rt_addresses - addresses_sent;
        }
        else{
            n_addresses_this_message = size_extra;
        }
    }
    return n_addresses_this_message;
}

//! \brief sets up the first packet to fly to the compressor core
//! \param[in] total_packets: how many packets going to be sent
//! \param[in] compressed_address: the address for compressed routing table
//! \param[in] n_rt_addresses: how many bit field addresses.
//! \param[in] n_addresses_this_message: the addresses to put in this
void set_up_first_packet(
        uint32_t total_packets, address_t compressed_address,
        uint32_t n_rt_addresses, uint32_t n_addresses_this_message){
    my_msg.data[COMMAND_CODE] = START_DATA_STREAM;

    // create cast
    start_stream_sdp_packet_t* data = (start_stream_sdp_packet_t*)
        &my_msg.data[START_OF_SPECIFIC_MESSAGE_DATA];

    // fill in
    data->n_sdp_packets_till_delivered = total_packets;
    data->address_for_compressed = compressed_address;
    data->fake_heap_data = user_register_content[USABLE_SDRAM_REGIONS];
    data->total_n_tables = n_rt_addresses;
    data->n_tables_in_packet = n_addresses_this_message;
    log_info(
        "mem cpy tables to dest = %d, from source = %d, bytes = %d",
        &data->tables[0], &bit_field_routing_tables[0],
        n_addresses_this_message * WORD_TO_BYTE_MULTIPLIER);

    sark_mem_cpy(
        &data->tables[0], &bit_field_routing_tables[0],
        n_addresses_this_message * WORD_TO_BYTE_MULTIPLIER);
    my_msg.length = (
        LENGTH_OF_SDP_HEADER + (
            (n_addresses_this_message + sizeof(start_stream_sdp_packet_t)) *
            WORD_TO_BYTE_MULTIPLIER));
    log_info(
        "message contains command code %d, n sdp packets till "
        "delivered %d, address for compressed %d, fake heap data "
        "address %d total n tables %d, n tables in packet %d",
        my_msg.data[COMMAND_CODE], data->n_sdp_packets_till_delivered,
        data->address_for_compressed, data->fake_heap_data,
        data->total_n_tables);
    for(uint32_t rt_id = 0; rt_id < n_addresses_this_message; rt_id++){
        log_info("table address is %d", data->tables[rt_id]);
    }
    log_info("message length = %d", my_msg.length);
}

//! \brief sets up the extra packet format
//! \param[in] n_addresses_this_message: n addresses to put into this message
//! \param[in] addresses_sent: how many addresses have already been sent.
void setup_extra_packet(
        uint32_t n_addresses_this_message, uint32_t addresses_sent){
    my_msg.data[COMMAND_CODE] = EXTRA_DATA_STREAM;
    extra_stream_sdp_packet_t* data =(extra_stream_sdp_packet_t*)
        my_msg.data[START_OF_SPECIFIC_MESSAGE_DATA];
    data->n_tables_in_packet = n_addresses_this_message;
    sark_mem_cpy(
        &data->tables, &bit_field_routing_tables[addresses_sent],
        n_addresses_this_message * WORD_TO_BYTE_MULTIPLIER);
    my_msg.length = (
        LENGTH_OF_SDP_HEADER + (
            (n_addresses_this_message + sizeof(extra_stream_sdp_packet_t)) *
            WORD_TO_BYTE_MULTIPLIER));
    log_info("message length = %d", my_msg.length);
}


//! \brief sends a SDP message to a compressor core to do compression with
//!  a number of bitfields
//! \param[in] n_rt_addresses: how many addresses the bitfields merged
//!  into
//! \param[in] mid_point: the mid point in the binary search
bool set_off_bit_field_compression(
        uint32_t n_rt_addresses, uint32_t mid_point){

    // allocate space for the compressed routing entries
    address_t compressed_address = MALLOC_SDRAM(
        routing_table_sdram_size_of_table(TARGET_LENGTH));
    if (compressed_address == NULL){
        log_error("failed to allocate sdram for compressed routing entries");
        return false;
    }
    log_info("address for compressed data is %d", compressed_address);

    // select compressor core to execute this
    uint32_t comp_core_id = select_compressor_core(mid_point);

    // record addresses for response processing code
    bool suc = record_address_data_for_response_functionality(
        n_rt_addresses, comp_core_id, compressed_address);
    if (!suc){
        log_error("failed to store the addresses for response functionality");
        return false;
    }

    // update sdp to right destination
    update_mc_message(comp_core_id);

    // deduce how many packets
    uint32_t total_packets = deduce_total_packets(n_rt_addresses);

    // generate the packets and fire them to the compressor core
    uint32_t addresses_sent = 0;
    for (uint32_t packet_id =0; packet_id < total_packets; packet_id++){
        // if just one packet worth, set to left over addresses
        uint32_t n_addresses_this_message = deduce_elements_this_packet(
            packet_id, n_rt_addresses, addresses_sent);

        // set data components
        if (packet_id == 0){  // first packet
            set_up_first_packet(
                total_packets, compressed_address, n_rt_addresses,
                n_addresses_this_message);
        }
        else{  // extra packets
            log_info("sending extra packet id = %d", packet_id);
            setup_extra_packet(n_addresses_this_message, addresses_sent);
        }

        // update location in addresses
        addresses_sent += n_addresses_this_message;

        // send sdp packet
        send_sdp_message();
    }

    return true;
}

//! \brief try running compression on just the uncompressed (attempt to check
//!     that without bitfields compression will work).
//! \return bool saying success or failure of the compression
bool start_binary_search(){

    // deduce how far to space these testers
    uint32_t hops_between_compression_cores =
        n_bf_addresses / n_available_compression_cores;
    uint32_t multiplier = 1;

    bool failed_to_malloc = false;

    // iterate till either ran out of cores, or failed to malloc sdram during
    // the setup of a core
    while (n_available_compression_cores != 0 || !failed_to_malloc){

        // try to create bitfield tables for a given point in the search
        uint32_t* n_rt_addresses;
        bool success = create_bit_field_router_tables(
            hops_between_compression_cores * multiplier, n_rt_addresses);

        // if successful, try setting off the bitfield compression
        if (success){
            success = set_off_bit_field_compression(
                n_rt_addresses, hops_between_compression_cores * multiplier);

             // if successful, move to next search point.
             if (success){
                 multiplier ++;
             }
             else{  // failed by malloc
                failed_to_malloc = true;
             }
        }
        else{  // failed by malloc
            failed_to_malloc = true;
        }
    }
    
    // if it did not set off 1 compression. fail fully. coz it wont ever get
    // anything done. host will pick up the slack
    if (multiplier == 1){
        return false;
    }
    
    // set off at least one compression, but at some point failed to malloc 
    // sdram. assume this is the cap on how many cores can be ran at any 
    // given time
    if (failed_to_malloc){
        n_available_compression_cores = 0;
    }
    
    // say we've started
    return true;
}

//! \brief compress the bitfields from the best location
void carry_on_binary_search(){

}

//! \brief removes the merged bitfields from the application cores bitfield
//!        regions
void remove_merged_bitfields_from_cores(){

}

//! \brief frees sdram from the compressor core.
//! \param[in] the compressor core to clear sdram usage from
//! \return bool stating that it was successful in clearing sdram
bool free_sdram_from_compression_attempt(uint32_t comp_core_id){
    uint32_t elements = comp_cores_bf_tables[
        comp_core_id]->n_elements;
    for (uint32_t core_bit_field_id = 0; core_bit_field_id < elements;
            core_bit_field_id++){
        FREE(comp_cores_bf_tables[
            comp_core_id]->elements[core_bit_field_id]);
    }
    return true;
}

//! \brief processes the response from the compressor attempt
//! \param[in] comp_core_id: the compressor core id
//! \param[in] the response code / finished state
void process_compressor_response(
        uint32_t comp_core_id, uint32_t finished_state){
    
    // filter off finished state
    if (finished_state == SUCCESSFUL_COMPRESSION){
        bit_field_set(tested_mid_points, c_core_mid_point[comp_core_id]);
        bit_field_set(
            mid_points_successes, c_core_mid_point[comp_core_id]);
        c_core_mid_point[comp_core_id] = DOING_NOWT;
        n_available_compression_cores ++;

        // kill any search below this point, as they all successful if this one
        // was / redundant as this is a better search.

        // free the sdram associated with this compressor core.
        bool success = free_sdram_from_compression_attempt(comp_core_id);
        if (!success){
            log_error("failed to free sdram for compressor core %d. WTF",
                      comp_core_id);
        }
    }
    else if (finished_state == FAILED_MALLOC){
        // this will threshold the number of compressor cores that
        // can be ran at any given time.
        c_core_mid_point[comp_core_id] = DOING_NOWT;
        // free the sdram associated with this compressor core.
        bool success = free_sdram_from_compression_attempt(comp_core_id);
        if (!success){
            log_error("failed to free sdram for compressor core %d. WTF",
                      comp_core_id);
        }
    }
    else if (finished_state == FAILED_TO_COMPRESS){
        // it failed to compress, so it was successful in malloc.
        // so mark the midpoint as tested, and free the core for another
        // attempt
        bit_field_set(tested_mid_points, c_core_mid_point[comp_core_id]);
        int compression_mid_point = c_core_mid_point[comp_core_id];
        c_core_mid_point[comp_core_id] = DOING_NOWT;
        n_available_compression_cores ++;
    
        // set all indices above this one to false, as this one failed
        for(uint32_t test_index = compression_mid_point;
                test_index < n_bf_addresses; test_index++){
            bit_field_set(tested_mid_points, test_index);
        }
    
        // tell all compression cores trying midpoints above this one
        // to stop, as its highly likely a waste of time.
        for (uint32_t check_core_id = 0;
                check_core_id < n_compression_cores; check_core_id++){
            if (c_core_mid_point[check_core_id] > compression_mid_point){
                send_sdp_force_stop_message(check_core_id);
            }
        }

        // free the sdram associated with this compressor core.
        bool success = free_sdram_from_compression_attempt(comp_core_id);
        if (!success){
            log_error("failed to free sdram for compressor core %d. WTF",
                      comp_core_id);
        }
    }
    else if (finished_state == RAN_OUT_OF_TIME){
        // if failed to compress by the end user considered QoS. So it
        // was successful in malloc. So mark the midpoint as tested,
        // and free the core for another attempt
        bit_field_set(tested_mid_points, c_core_mid_point[comp_core_id]);
        c_core_mid_point[comp_core_id] = DOING_NOWT;
        n_available_compression_cores ++;

        // free the sdram associated with this compressor core.
        bool success = free_sdram_from_compression_attempt(comp_core_id);
        if (!success){
            log_error("failed to free sdram for compressor core %d. WTF",
                      comp_core_id);
        }
    }
    else if (finished_state == FORCED_BY_COMPRESSOR_CONTROL){
        // this gives no context of why the control killed it. just
        // free the core for another attempt
        c_core_mid_point[comp_core_id] = DOING_NOWT;
        n_available_compression_cores ++;

        // free the sdram associated with this compressor core.
        bool success = free_sdram_from_compression_attempt(comp_core_id);
        if (!success){
            log_error("failed to free sdram for compressor core %d. WTF",
                      comp_core_id);
        }
    }
    else{
        log_error("no idea what to do with finished state %d, from "
                  "core %d ignoring", finished_state, comp_core_id);
    }
    if (n_available_compression_cores > 0){
        carry_on_binary_search();
    }
}

//! \brief the sdp control entrance.
//! \param[in] mailbox: the message
//! \param[in] port: don't care.
void _sdp_handler(uint mailbox, uint port) {
    use(port);
    // get data from the sdp message
    sdp_msg_pure_data *msg = (sdp_msg_pure_data *) mailbox;
    log_info("received response");
    log_info("command code is %d", msg->data[COMMAND_CODE]);
    log_info("response code was %d", msg->data[START_OF_SPECIFIC_MESSAGE_DATA]);

    // filter off the port we've decided to use for this
    if (msg->srce_port >> PORT_SHIFT == RANDOM_PORT){

        // filter based off the command code. Anything thats not a response is
        // a error
        if (msg->data[COMMAND_CODE] == START_DATA_STREAM){
            log_error(
                "no idea why im receiving a start data message. Ignoring");
            sark_msg_free((sdp_msg_t*) msg);
        }
        else if (msg->data[COMMAND_CODE] == EXTRA_DATA_STREAM){
            log_error(
                "no idea why im receiving a extra data message. Ignoring");
            sark_msg_free((sdp_msg_t*) msg);
        }
        else if(msg->data[COMMAND_CODE] == COMPRESSION_RESPONSE){
            // locate the compressor core id that responded
            uint32_t comp_core_id = (msg->srce_port && CORE_MASK);

            // response code just has one value, so being lazy and not casting
            uint32_t finished_state = msg->data[START_OF_SPECIFIC_MESSAGE_DATA];

            // free message now, nothing left in it
            sark_msg_free((sdp_msg_t*) msg);
            
            process_compressor_response(comp_core_id, finished_state);
        }
        else if (msg->data[COMMAND_CODE] == STOP_COMPRESSION_ATTEMPT){
            log_error(
                "no idea why im receiving a stop message. Ignoring");
            sark_msg_free((sdp_msg_t*) msg);
        }
        else{
            log_error(
                "no idea what to do with message with command code %d Ignoring",
                msg->data[COMMAND_CODE]);
            sark_msg_free((sdp_msg_t*) msg);
        }
    }
    else{
        log_error(
            "no idea what to do with message. on port %d Ignoring",
            msg->srce_port >> PORT_SHIFT);
        sark_msg_free((sdp_msg_t*) msg);
    }
}


//! \brief reads in the addresses region and from there reads in the key atom
// map and from there searches for a given key. when found, returns the n atoms
//! \param[in] key: the key to locate n atoms for
//! \return atom for the key
uint32_t locate_key_atom_map(uint32_t key){
    // locate n address pairs
    uint32_t position_in_address_region = 0;
    uint32_t n_address_pairs =
        user_register_content[REGION_ADDRESSES][
            position_in_address_region];

    // cycle through key to atom regions to locate key
    position_in_address_region += 1;
    for (uint32_t region_id = 0; region_id < n_address_pairs; region_id++){
        // get key address region
        address_t key_atom_sdram_address =
            (address_t) user_register_content[REGION_ADDRESSES][
                position_in_address_region + KEY_TO_ATOM_REGION];

        // read how many keys atom pairs there are
        uint32_t position_ka_pair = 0;
        uint32_t n_key_atom_pairs = key_atom_sdram_address[position_ka_pair];
        log_debug("n key pairs to check are %d", n_key_atom_pairs);
        position_ka_pair += 1;

        // cycle through keys in this region looking for the key find atoms of
        for (uint32_t key_atom_pair_id = 0; key_atom_pair_id <
                n_key_atom_pairs; key_atom_pair_id++){
            uint32_t key_to_check = 
                key_atom_sdram_address[position_ka_pair + SRC_BASE_KEY];
            log_debug("key to check = %d", key_to_check);

            // if key is correct, return atoms
            if (key_to_check == key){
                log_debug(
                    "found key, returning n atoms of %d",
                     key_atom_sdram_address[position_ka_pair + SRC_N_ATOMS]);
                return key_atom_sdram_address[
                    position_ka_pair + SRC_N_ATOMS];
            }

            // move to next key pair
            position_ka_pair += LENGTH_OF_KEY_ATOM_PAIR;
        }

        // move to next key to atom sdram region
        position_in_address_region += ADDRESS_PAIR_LENGTH;
    }
    log_error("cannot find the key %d at all?! WTF", key);
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
    sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_FAIL;
    rt_error(RTE_SWERR);
    return 0;
}

//! \brief Load a routing table to the router.
//! \return bool saying if the table was loaded into the router or not
void load_routing_table_entries_to_router() {

    // Try to allocate sufficient room for the routing table.
    uint32_t entry_id = rtr_alloc_id(
        last_compressed_table.size,
        user_register_content[UNCOMP_ROUTER_TABLE][APPLICATION_APP_ID]);

    if (entry_id == 0) {
        log_error("Unable to allocate routing table of size %u\n",
                  last_compressed_table.size);
        vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
        sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_MALLOC;
    }

    // Load entries into the table (provided the allocation succeeded).
    // Note that although the allocation included the specified
    // application ID we also need to include it as the most significant
    // byte in the route (see `sark_hw.c`).
    for (uint32_t i = 0; i < last_compressed_table.size; i++) {
        // extract entry from table
        entry_t entry = last_compressed_table.entries[i];
        // merge app id to route
        uint32_t route = entry.route | (app_id << ROUTE_APP_ID_BIT_SHIFT);
        // set on the router
        rtr_mc_set(
            entry_id + i, entry.key_mask.key, entry.key_mask.mask, route);
    }
}

//! \brief reads a bitfield and deduces how many bits are not set
uint32_t detect_redundant_packet_count(address_t bit_field_struct){
    log_debug("address's location is %d", bit_field_struct);
    log_debug(" key is %d", bit_field_struct[BIT_FIELD_BASE_KEY]);
    uint32_t n_filtered_packets = 0;
    uint32_t n_neurons =
        locate_key_atom_map(bit_field_struct[BIT_FIELD_BASE_KEY]);
    for (uint neuron_id = 0; neuron_id < n_neurons; neuron_id++){
        if (!bit_field_test(
                (bit_field_t) &bit_field_struct[START_OF_BIT_FIELD_DATA],
                 neuron_id)){
            n_filtered_packets += 1;
        }
    }
    log_debug("n filtered packets = %d", n_filtered_packets);
    return n_filtered_packets;
}

//! \brief do some location and addition stuff
//! \param[in]
//! \param[in]
//! \param[in]
//! \param[in]
//! \param[in]
//! \param[in]
//! \return the new covered level
uint32_t locate_and_add_bit_fields(
    _coverage** coverage, uint32_t coverage_index, uint32_t *cores_to_add_for,
    uint32_t cores_to_add_length, uint32_t diff, uint32_t covered){
    for (uint32_t processor_id_index =0;
            processor_id_index < coverage[coverage_index]->length_of_list;
            processor_id_index++){
        // check for the processor id's in the cores to add from, and add the
        // bitfield with that redundant packet rate and processor to the sorted
        // bitfields
        uint32_t processor_id_to_check = coverage[
            coverage_index]->processor_ids[processor_id_index];

        // look inside cores to add for
        for (uint32_t processor_to_check_index=0;
                processor_to_check_index<cores_to_add_length;
                processor_to_check_index++){
            uint32_t processor_id_to_work_on =
                cores_to_add_for[processor_to_check_index];
            if(processor_id_to_check == processor_id_to_work_on){
                if (covered < diff){
                    // add to sorted bitfield
                    covered += 1;
                    sorted_bit_fields[sorted_bit_field_current_fill_loc] =
                        coverage[coverage_index]->bit_field_addresses[
                            processor_to_check_index];
                    sorted_bit_field_current_fill_loc += 1;

                    // delete (aka set to null, to bypass lots of data moves)
                    coverage[coverage_index]->bit_field_addresses[
                            processor_to_check_index] = NULL;
                    coverage[coverage_index]->processor_ids[
                        processor_to_check_index] = NULL;
                }
            }
        }
    }
    return covered;
}

//! \brief orders the bitfields for the binary search based off the impact
//! made in reducing the redundant packet processing on cores.
//! \param[in] _bit_field_by_coverage:
//! \param[in] proc_cov_by_bit_field:
//! \param[in] n_pairs: the number of processors/elements to search
//! \param[in] n_unique_redundant_packet_counts: the count of how many unique
//!      redundant packet counts there are.
//! \return None
void order_bit_fields_based_on_impact(
        _coverage** coverage,
        _proc_cov_by_bitfield_t** proc_cov_by_bit_field, uint32_t n_pairs,
        uint32_t n_unique_redundant_packet_counts){

    // sort processor coverage by bitfield so that ones with longest length are
    // at the front of the list
    bool moved = true;
    while (moved){
        moved = false;
        _proc_cov_by_bitfield_t* element = proc_cov_by_bit_field[0];
        for (uint index = 1; index < n_pairs; index ++){
            _proc_cov_by_bitfield_t* compare_element =
                proc_cov_by_bit_field[index];
            if (element->length_of_list < compare_element->length_of_list){
                // create temp holder for moving objects
                _proc_cov_by_bitfield_t* temp_pointer;
                // move to temp
                temp_pointer = element;
                // move compare over to element
                proc_cov_by_bit_field[index - 1] = compare_element;
                // move element over to compare location
                proc_cov_by_bit_field[index] = temp_pointer;
                // update flag
                moved = true;
            }
            else{
                element = proc_cov_by_bit_field[index];
            }
        }
    }

    // move bit_fields over from the worst affected cores. The list of worst
    // affected cores will grow in time as the worst cores are balanced out
    // by the redundant packets being filtered by each added bitfield.
    uint32_t cores_to_add_for[n_pairs];
    uint32_t cores_to_add_length = 0;

    // go through all cores but last 1
    for (uint32_t worst_core_id = 0; worst_core_id < n_pairs - 1;
            worst_core_id++){

        // add worst core to set to look for bitfields in
        cores_to_add_for[cores_to_add_length] =
            proc_cov_by_bit_field[worst_core_id]->processor_id;
        cores_to_add_length += 1;

        // determine difference between the worst and next worst
        uint32_t diff = proc_cov_by_bit_field[worst_core_id]->length_of_list -
             proc_cov_by_bit_field[worst_core_id + 1]->length_of_list;

        // sort by bubble sort so that the most redundant packet count
        // addresses are at the front
        bool moved = true;
        while (moved){
            moved = false;
            uint32_t element =
                proc_cov_by_bit_field[worst_core_id]->redundant_packets[0];
            for (uint index = 1; index < n_pairs; index ++){
                uint32_t compare_element = proc_cov_by_bit_field[
                        worst_core_id]->redundant_packets[index];
                if (element < compare_element){
                    uint32_t temp_value = 0;
                    // move to temp
                    temp_value = element;
                    // move compare over to element
                    proc_cov_by_bit_field[worst_core_id]->redundant_packets[
                        index - 1] = compare_element;
                    // move element over to compare location
                    proc_cov_by_bit_field[worst_core_id]->redundant_packets[
                        index] = temp_value;
                    // update flag
                    moved = true;
                }
                else{
                    element = proc_cov_by_bit_field[
                        worst_core_id]->redundant_packets[index];
                }
            }
        }

        // cycle through the list of a cores redundant packet counts and locate
        // the bitfields which match up
        uint32_t covered = 0;
        for (uint32_t redundant_packet_count_index = 0;
                redundant_packet_count_index <
                proc_cov_by_bit_field[worst_core_id]->length_of_list;
                redundant_packet_count_index ++){

            // the coverage packet count to try this time
            uint32_t x_redundant_packets = proc_cov_by_bit_field[
                worst_core_id]->redundant_packets[redundant_packet_count_index];

            // locate the bitfield with coverage that matches the x redundant
            // packets
            for (uint32_t coverage_index = 0; 
                    coverage_index < n_unique_redundant_packet_counts;
                    coverage_index++){
                if (coverage[coverage_index]->n_redundant_packets ==
                        x_redundant_packets){
                    covered = locate_and_add_bit_fields(
                        coverage, coverage_index, cores_to_add_for,
                        cores_to_add_length, diff, covered);
                }
            }
        }
    }

    // sort bitfields by coverage by n_redundant_packets so biggest at front
    moved = true;
    while (moved){
        moved = false;
        _coverage* element = coverage[0];
        for (uint index = 1; index < n_unique_redundant_packet_counts;
                index ++){
            _coverage* compare_element = coverage[index];
            if (element->n_redundant_packets <
                    compare_element->n_redundant_packets){
                _coverage* temp_pointer;
                // move to temp
                temp_pointer = element;
                // move compare over to element
                coverage[index - 1] = compare_element;
                // move element over to compare location
                coverage[index] = temp_pointer;
                // update flag
                moved = true;
            }
            else{
                element = coverage[index];
            }
        }
    }

    // iterate through the coverage and add any that are left over.
    for (uint index = 0; index < n_unique_redundant_packet_counts;
            index ++){
        for (uint32_t bit_field_index = 0;
                bit_field_index < coverage[index]->length_of_list;
                bit_field_index++){
            if (coverage[index]->bit_field_addresses[bit_field_index] != NULL){
                sorted_bit_fields[sorted_bit_field_current_fill_loc] =
                        coverage[index]->bit_field_addresses[bit_field_index];
                sorted_bit_fields_processor_ids[
                    sorted_bit_field_current_fill_loc] = coverage[
                        index]->processor_ids[bit_field_index];
                sorted_bit_field_current_fill_loc += 1;
            }
        }
    }
}

//! \brief sets off the basic compression without any bitfields
bool set_off_no_bit_field_compression(){

    // allocate and clone uncompressed entry
    address_t* sdram_clone_of_routing_table;
    bool suc = clone_un_compressed_routing_table(sdram_clone_of_routing_table);
    if (!suc){
        log_error("could not allocate memory for uncompressed table for no "
                  "bit field compression attempt.");
        return false;
    }

    // set up the bitfield routing tables so that it'll map down below
    bit_field_routing_tables = MALLOC(sizeof(address_t*));
    bit_field_routing_tables[0] = sdram_clone_of_routing_table;

    // run the allocation and set off of a compressor core
    return set_off_bit_field_compression(N_UNCOMPRESSED_TABLE, 0);
}

//! \brief reads in bitfields, makes a few maps, sorts into most priority.
//! \return bool that states if it succeeded or not.
bool read_in_bit_fields(){

    // count how many bitfields there are in total
    uint position_in_region_data = 0;
    n_bf_addresses = 0;
    uint32_t n_pairs_of_addresses =
        user_register_content[REGION_ADDRESSES][N_PAIRS];
    position_in_region_data = START_OF_ADDRESSES_DATA;
    //log_info("n pairs of addresses = %d", n_pairs_of_addresses);

    // malloc the bt fields by processor
    //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
    bit_field_by_processor = MALLOC(
        n_pairs_of_addresses * sizeof(_bit_field_by_processor_t));
    if (bit_field_by_processor == NULL){
        log_error("failed to allocate memory for pairs, if it fails here. "
                  "might as well give up");
        return false;
    }
    
    // build processor coverage by bitfield
    //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
    _proc_cov_by_bitfield_t** proc_cov_by_bitfield = MALLOC(
        n_pairs_of_addresses * sizeof(_proc_cov_by_bitfield_t*));
    if (proc_cov_by_bitfield == NULL){
        log_error("failed to allocate memory for processor coverage by "
                  "bitfield, if it fails here. might as well give up");
        return false;
    }

    // iterate through a processors bitfield region and get n bitfields
    for (uint region_id = 0; region_id < n_pairs_of_addresses; region_id++){
        
        // malloc for n redundant packets
        //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
        proc_cov_by_bitfield[region_id] = MALLOC(sizeof(
            _proc_cov_by_bitfield_t));
        if (proc_cov_by_bitfield[region_id] == NULL){
            log_error("failed to allocate memory for processor coverage for "
                      "region %d. might as well give up", region_id);
            return false;
        }

        // track processor id
        bit_field_by_processor[region_id].processor_id =
            user_register_content[REGION_ADDRESSES][
                position_in_region_data + PROCESSOR_ID];
        proc_cov_by_bitfield[region_id]->processor_id =
            user_register_content[REGION_ADDRESSES][
                position_in_region_data + PROCESSOR_ID];
        //log_info("bit_field_by_processor in region %d processor id = %d",
        //         region_id, bit_field_by_processor[region_id].processor_id);

        // locate data for malloc memory calcs
        address_t bit_field_address = (address_t) user_register_content[
            REGION_ADDRESSES][position_in_region_data + BITFIELD_REGION];
        position_in_region_data += ADDRESS_PAIR_LENGTH;
        uint32_t pos_in_bitfield_region = N_BIT_FIELDS;
        uint32_t core_n_bit_fields = bit_field_address[pos_in_bitfield_region];
        pos_in_bitfield_region = START_OF_BIT_FIELD_TOP_DATA;
        n_bf_addresses += core_n_bit_fields;
        
        // track lengths
        proc_cov_by_bitfield[region_id]->length_of_list = core_n_bit_fields;
        bit_field_by_processor[region_id].length_of_list = core_n_bit_fields;
        //log_info("bit field by processor with region %d, has length of %d",
        //         region_id, core_n_bit_fields);
        
        // malloc for bitfield region addresses
        //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
        bit_field_by_processor[region_id].bit_field_addresses = MALLOC(
            core_n_bit_fields * sizeof(address_t));
        if (bit_field_by_processor[region_id].bit_field_addresses == NULL){
            log_error("failed to allocate memory for bitfield addresses for "
                      "region %d, might as well fail", region_id);
            return false; 
        }
        
        // malloc for n redundant packets
        //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
        proc_cov_by_bitfield[region_id]->redundant_packets = MALLOC(
            core_n_bit_fields * sizeof(uint));
        if (proc_cov_by_bitfield[region_id]->redundant_packets == NULL){
            log_error("failed to allocate memory for processor coverage for "
                      "region %d, might as well fail", region_id);
            return false;
        }

        // populate tables: 1 for addresses where each bitfield component starts
        //                  2 n redundant packets
        for (uint32_t bit_field_id = 0; bit_field_id < core_n_bit_fields;
                bit_field_id++){
            bit_field_by_processor[region_id].bit_field_addresses[
                bit_field_id] =
                    (address_t) bit_field_address[pos_in_bitfield_region];

            uint32_t n_redundant_packets =
                detect_redundant_packet_count(
                    (address_t) &bit_field_address[pos_in_bitfield_region]);
            proc_cov_by_bitfield[region_id]->redundant_packets[bit_field_id] =
                n_redundant_packets;
            //log_info("prov cov by bitfield for region %d, redundant packets "
            //         "at index %d, has n redundant packets of %d",
            //         region_id, bit_field_id, n_redundant_packets);
            
            pos_in_bitfield_region += 
                START_OF_BIT_FIELD_DATA + bit_field_address[
                    pos_in_bitfield_region + BIT_FIELD_N_WORDS];
        }
    }

    // sort out teh searcher bitfields. as now first time where can do so
    bool success = set_up_search_bitfields();
    if (!success){
        log_error("can not allocate memory for search fields.");
        return false;
    }

    // set off a none bitfield compression attempt, to pipe line work
    log_info("sets off the uncompressed version of the search");
    set_off_no_bit_field_compression();

    // populate the bitfield by coverage
    //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
    sorted_bit_fields = MALLOC(n_bf_addresses * sizeof(address_t));
    if(sorted_bit_fields == NULL){
        log_error("cannot allocate memory for the sorted bitfield addresses");
        return false;
    }

    //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
    sorted_bit_fields_processor_ids =
        MALLOC(n_bf_addresses * sizeof(uint32_t));
    if (sorted_bit_fields_processor_ids == NULL){
        log_error("cannot allocate memory for the sorted bitfields with "
                  "processors ids");
        return false;
    }

    uint length_n_redundant_packets = 0;
    //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
    uint * redundant_packets = MALLOC(n_bf_addresses * sizeof(uint));

    // filter out duplicates in the n redundant packets
    position_in_region_data = START_OF_ADDRESSES_DATA;
    for (uint region_id = 0; region_id < n_pairs_of_addresses; region_id++){
        // cycle through the bitfield registers again to get n bitfields per
        // core
        address_t bit_field_address =
            (address_t) user_register_content[REGION_ADDRESSES][
                position_in_region_data + BITFIELD_REGION];
        position_in_region_data += ADDRESS_PAIR_LENGTH;
        uint32_t core_n_bit_fields = bit_field_address[N_BIT_FIELDS];

        // check that each bitfield redundant packets are unqiue and add to set
        for (uint32_t bit_field_id = 0; bit_field_id < core_n_bit_fields;
                bit_field_id++){
            uint x_packets = proc_cov_by_bitfield[
                region_id]->redundant_packets[bit_field_id];
            // check if seen this before
            bool found = false;
            for (uint index = 0; index < length_n_redundant_packets; index++){
                if(redundant_packets[index] == x_packets){
                    found = true;
                }
            }
            // if not a duplicate, add to list and update size
            if (!found){
                redundant_packets[length_n_redundant_packets] = x_packets;
                length_n_redundant_packets += 1;
            }
        }
    }
    //log_info("length of n redundant packets = %d", length_n_redundant_packets);

    // malloc space for the bitfield by coverage map
    //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
    _coverage** coverage = MALLOC(
        length_n_redundant_packets * sizeof(_coverage*));
    if (coverage == NULL){
        log_error("failed to malloc memory for the bitfields by coverage. "
                  "might as well fail");
        return false;
    }
    
    // go through the unique x redundant packets and build the list of 
    // bitfields for it
    for (uint32_t r_packet_index = 0; 
            r_packet_index < length_n_redundant_packets; r_packet_index++){
        // malloc a redundant packet entry
        //log_info("try to allocate memory of size %d for coverage at index %d",
        //         sizeof(_coverage), r_packet_index);
        //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
        coverage[r_packet_index] = MALLOC(sizeof(_coverage));
        if (coverage[r_packet_index] == NULL){
            log_error("failed to malloc memory for the bitfields by coverage "
                      "for index %d. might as well fail", r_packet_index);
            return false;
        }
        
        // update the redundant packet pointer
        coverage[r_packet_index]->n_redundant_packets = 
            redundant_packets[r_packet_index];
        
        // search to see how long the list is going to be.
        uint32_t n_bit_fields_with_same_x_r_packets = 0;
        for (uint region_id = 0; region_id < n_pairs_of_addresses; region_id++){
            uint length = proc_cov_by_bitfield[region_id]->length_of_list;
            for(uint red_packet_index = 0; red_packet_index < length;
                    red_packet_index ++){
                if(proc_cov_by_bitfield[region_id]->redundant_packets[
                        red_packet_index] == redundant_packets[r_packet_index]){
                    n_bit_fields_with_same_x_r_packets += 1;
                }
            }
        }
        
        // update length of list
        coverage[r_packet_index]->length_of_list = 
            n_bit_fields_with_same_x_r_packets;
        
        // malloc list size for these addresses of bitfields with same 
        // redundant packet counts.
        //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
        coverage[r_packet_index]->bit_field_addresses = MALLOC(
            n_bit_fields_with_same_x_r_packets * sizeof(address_t));
        if(coverage[r_packet_index]->bit_field_addresses == NULL){
            log_error("failed to allocate memory for the coverage on index %d"
                      " for addresses. might as well fail.", r_packet_index);
            return false;
        }
        
        // malloc list size for the corresponding processors ids for the 
        // bitfields
        //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
        //log_info(
        //    "trying to allocate %d bytes, for x bitfields same xr packets %d",
        //    n_bit_fields_with_same_x_r_packets * sizeof(uint32_t),
         //   n_bit_fields_with_same_x_r_packets);
        coverage[r_packet_index]->processor_ids = MALLOC(
            n_bit_fields_with_same_x_r_packets * sizeof(uint32_t));
        if(coverage[r_packet_index]->processor_ids == NULL){
            log_error("failed to allocate memory for the coverage on index %d"
                      " for processors. might as well fail.", r_packet_index);
            return false;
        }
            
        // populate list of bitfields addresses which have same redundant 
        //packet count.
        //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
        //log_info(
        //    "populating list of bitfield addresses with same packet count");
        for (uint region_id = 0; region_id < n_pairs_of_addresses; region_id++){
            //log_info("prov cov for region id %d has length %d", region_id,
            //         proc_cov_by_bitfield[region_id]->length_of_list);
            uint32_t length = proc_cov_by_bitfield[region_id]->length_of_list;
            uint32_t processor_id_index = 0;
            for(uint red_packet_index = 0; red_packet_index < length;
                    red_packet_index ++){

                if(proc_cov_by_bitfield[region_id]->redundant_packets[
                        red_packet_index] == redundant_packets[r_packet_index]){
                    coverage[r_packet_index]->bit_field_addresses[
                        processor_id_index] = bit_field_by_processor[
                            region_id].bit_field_addresses[red_packet_index];
                    coverage[r_packet_index]->processor_ids[processor_id_index]
                        = bit_field_by_processor[region_id].processor_id;
                    processor_id_index += 1;
                }
            }
        }
        //log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
    }

    // free the redundant packet tracker, as now tailored ones are in the dict
    FREE(redundant_packets);

    // order the bitfields based off the impact to cores redundant packet
    // processing
    order_bit_fields_based_on_impact(
        coverage, proc_cov_by_bitfield, n_pairs_of_addresses,
        length_n_redundant_packets);

    // free the data holders we don't care about now that we've got our
    // sorted bitfields list
    for(uint region_id = 0; region_id < n_pairs_of_addresses; region_id++){
        _coverage* cov_element = coverage[region_id];
        FREE(cov_element->bit_field_addresses);
        FREE(cov_element->processor_ids);
        FREE(cov_element);
        _proc_cov_by_bitfield_t* proc_cov_element =
            proc_cov_by_bitfield[region_id];
        FREE(proc_cov_element->redundant_packets);
        FREE(proc_cov_element);
    }
    FREE(coverage);
    FREE(proc_cov_by_bitfield);

    // return success for reading in and sorting bitfields
    return true;
}

//! \brief starts the work for the compression search
bool start_process(){
    // will use this many palces. so exrtact at top
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;

    //log_info("read in bitfields");
    bool success_reading_in_bit_fields = read_in_bit_fields();
    //log_info("finished reading in bitfields");
    if (! success_reading_in_bit_fields){
        log_error("failed to read in bitfields, failing");
        sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_MALLOC;
        return false;
    }

    log_info("start binary search");
    bool success_start_binary_search = start_binary_search();
    log_info("finish binary search");

    if (!success_start_binary_search){
        log_error("failed to compress the routing table at all. Failing");
        sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_FAIL;
        return false;
    }
    
    return true;
}

void start_compression_process(){
    bool success = start_process();
    if (!success){
        rt_error(RTE_SWERR);
    }
}

//! \brief sets up a tracker for the user registers so that its easier to use
//!  during coding.
void initialise_user_register_tracker(){
    log_info("set up user register tracker (easier reading)");
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
    user_register_content[APPLICATION_POINTER_TABLE] =
        (address_t) sark_virtual_processor_info[spin1_get_core_id()].user0;
    user_register_content[UNCOMP_ROUTER_TABLE] =
        (address_t) sark_virtual_processor_info[spin1_get_core_id()].user1;
    user_register_content[REGION_ADDRESSES] =
        (address_t) sark_virtual_processor_info[spin1_get_core_id()].user2;
    user_register_content[USABLE_SDRAM_REGIONS] =
        (address_t) sark_virtual_processor_info[spin1_get_core_id()].user3;
    log_info("finished setting up register tracker: \n\n"
             "user0 = %d\n user1 = %d\n user2 = %d\n user3 = %d\n",
             user_register_content[APPLICATION_POINTER_TABLE],
             user_register_content[UNCOMP_ROUTER_TABLE],
             user_register_content[REGION_ADDRESSES],
             user_register_content[USABLE_SDRAM_REGIONS]);
}

//! \brief reads in router table setup params
void initialise_routing_control_flags(){
    address_t addresses_region =
        user_register_content[UNCOMP_ROUTER_TABLE];
    app_id = addresses_region[APPLICATION_APP_ID];
    total_entries_in_uncompressed_router_table = addresses_region[N_ENTRIES];
}

//! \brief get compressor cores
bool initialise_compressor_cores(){
    // locate the data point for compressor cores
    uint32_t n_region_pairs = user_register_content[REGION_ADDRESSES][N_PAIRS];
    uint32_t hop = 1 + (n_region_pairs * ADDRESS_PAIR_LENGTH);

    // get n compression cores and update trackers
    n_compression_cores =
        user_register_content[REGION_ADDRESSES][hop + N_COMPRESSOR_CORES];
    n_available_compression_cores = n_compression_cores;

    // malloc dtcm for this
    compressor_cores = MALLOC(n_compression_cores * sizeof(uint32_t));

    // verify malloc worked
    if (compressor_cores == NULL){
        log_error("failed to allocate memory for the compressor cores");
        return false;
    }

    // populate with compressor cores
    for (uint32_t core=0; core < n_compression_cores; core++){
        compressor_cores[core] = user_register_content[REGION_ADDRESSES][
            hop + N_COMPRESSOR_CORES + START_OF_comp_core_idS + core];
    }

    // allocate memory for the trackers
    c_core_mid_point = MALLOC(n_compression_cores * sizeof(int));
    if (c_core_mid_point == NULL){
        log_error("failed to allocate memory for tracking what the "
                  "compression cores are doing");
        return false;
    }

    // set the trackers all to -1 as starting point. to ensure completeness
    for (uint32_t core = 0; core < n_compression_cores; core++){
        c_core_mid_point[core] = DOING_NOWT;
    }

    // set up addresses tracker
    comp_cores_bf_tables = MALLOC(
        n_compression_cores * sizeof(comp_core_store*));
    if(comp_cores_bf_tables == NULL){
        log_error("failed to allocate memory for the holding of bitfield "
                  "addresses per compressor core");
        return false;
    }

    // set up counter for addresses tracker

    return true;
}

//! \brief the callback for setting off the router compressor
bool initialise() {
    log_info("Setting up stuff to allow bitfield compression control class to"
             " occur.");

    // Get pointer to 1st virtual processor info struct in SRAM
    initialise_user_register_tracker();

    // get the compressor data flags (app id, compress only when needed,
    //compress as much as possible, x_entries
    initialise_routing_control_flags();

    // get the compressor cores stored in a array
    bool success_compressor_cores = initialise_compressor_cores();
    if(!success_compressor_cores){
        log_error("failed to init the compressor cores.");
        return false;
    }

    // build the fake heap for allocating memory
    log_info("setting up fake heap for sdram usage");
    platform_new_heap_creation(user_register_content[USABLE_SDRAM_REGIONS]);
    log_info("finished setting up fake heap for sdram usage");
    return true;
}

//! \brief the main entrance.
void c_main(void) {
    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));

    bool success_init = initialise();
    if (!success_init){
        log_error("failed to init");
        rt_error(RTE_SWERR);
    }

    // kick-start the process
    spin1_schedule_callback(
        start_compression_process, 0, 0, COMPRESSION_START_PRIORITY);
    spin1_callback_on(SDP_PACKET_RX, _sdp_handler, SDP_PRIORITY);

    // go
    spin1_start(SYNC_WAIT);
    //spin1_pause
    //spin1_resume
}
