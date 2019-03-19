#include <spin1_api.h>
#include <debug.h>
#include <bit_field.h>
#include <sdp_no_scp.h>
#include "common-typedefs.h"
#include "../common/compressor_common/platform.h"
#include "../common/compressor_common/routing_table.h"
#include "../common/compressor_common/compression_sdp_formats.h"
#include "../common/compressor_common/constants.h"
#include "compressor_sorter_structs.h"
#include "sorters.h"
/*****************************************************************************/
/* SpiNNaker routing table minimisation with bitfield integration control core.
 *
 * controls the attempt to minimise the router entries with bitfield
 * components.
 */

//=============================================================================

//! enum mapping for elements in uncompressed routing table region
typedef enum uncompressed_routing_table_region_elements{
    APPLICATION_APP_ID = 0, N_ENTRIES = 1, START_OF_UNCOMPRESSED_ENTRIES = 2
} uncompressed_routing_table_region_elements;

//! enum for the compressor cores data elements (used for programmer debug)
typedef enum compressor_core_elements{
    N_COMPRESSOR_CORES = 0, START_OF_COMP_CORE_IDS = 1
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
    THRESHOLD = 0, N_PAIRS = 1, START_OF_ADDRESSES_DATA = 2
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

//! neuron level mask
#define NEURON_LEVEL_MASK 0xFFFFFFFF

//! how many tables the uncompressed router table entries is
#define N_UNCOMPRESSED_TABLE 1

//============================================================================

//! bool flag saying still reading in bitfields, so that state machine dont 
//! go boom when un compressed result comes in
bool reading_bit_fields = true;

//! bool flag for stopping multiple attempts to run carry on binary search
bool still_trying_to_carry_on = false;

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
table_t* last_compressed_table;

//! the compressor app id
uint32_t app_id = 0;

// how many bitfields there are
int n_bf_addresses = 0;

//! how many entries are in the uncompressed version
uint32_t total_entries_in_uncompressed_router_table = 0;

//! the list of bitfields in sorted order based off best effect.
address_t * sorted_bit_fields;

//! list of bitfield associated processor ids. sorted order based off best
//! effort linked to sorted_bit_fields, but separate to avoid sdram rewrites
uint32_t * sorted_bit_fields_processor_ids;

//! the list of the addresses of the routing table entries for the bitfields 
//! and reduced routing table
address_t * bit_field_routing_tables;

// the list of compressor cores to bitfield routing table sdram addresses
comp_core_store_t * comp_cores_bf_tables;

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
int * comp_core_mid_point;

//! the bitfield by processor global holder
_bit_field_by_processor_t* bit_field_by_processor;

//! the current length of the filled sorted bit field.
uint32_t sorted_bit_field_current_fill_loc = 0;

//! \brief sdp message to send control messages to compressors cores
sdp_msg_pure_data my_msg;

//============================================================================

//! \brief sends the sdp message. assumes all params have already been set
void send_sdp_message(){
    uint32_t attempt = 0;
    log_debug("sending message");
    while (!spin1_send_sdp_msg((sdp_msg_t *) &my_msg, _SDP_TIMEOUT)) {
        attempt +=1 ;
        log_info("failed to send. trying again");
        if (attempt >= 30){
            rt_error(RTE_SWERR);

        }
    }
    log_debug("sent message");
}

//! \brief Load the best routing table to the router.
//! \return bool saying if the table was loaded into the router or not
bool load_routing_table_into_router() {

    // Try to allocate sufficient room for the routing table.
    uint32_t start_entry = rtr_alloc_id(last_compressed_table->size, app_id);
    if (start_entry == 0) {
        log_error(
            "Unable to allocate routing table of size %u\n",
            last_compressed_table->size);
        return false;
    }

    // Load entries into the table (provided the allocation succeeded).
    // Note that although the allocation included the specified
    // application ID we also need to include it as the most significant
    // byte in the route (see `sark_hw.c`).
    log_info("loading %d entries into router", last_compressed_table->size);
    for (uint32_t entry_id = 0; entry_id < last_compressed_table->size;
            entry_id++) {
        entry_t entry = last_compressed_table->entries[entry_id];
        uint32_t route = entry.route | (app_id << ROUTE_APP_ID_BIT_SHIFT);
        rtr_mc_set(
            start_entry + entry_id, entry.key_mask.key, entry.key_mask.mask,
            route);
    }

    // Indicate we were able to allocate routing table entries.
    return true;
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

    // clear the bitfields
    clear_bit_field(tested_mid_points, get_bit_field_size(n_bf_addresses));
    clear_bit_field(mid_points_successes, get_bit_field_size(n_bf_addresses));

    // return if successful
    return true;
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
            position_in_address_region + N_PAIRS];

    // cycle through key to atom regions to locate key
    position_in_address_region += START_OF_ADDRESSES_DATA;
    for (uint32_t r_id = 0; r_id < n_address_pairs; r_id++){
        // get key address region
        address_t key_atom_sdram_address =
            (address_t) user_register_content[REGION_ADDRESSES][
                position_in_address_region + KEY_TO_ATOM_REGION];

        // read how many keys atom pairs there are
        uint32_t position_ka_pair = 0;
        uint32_t n_key_atom_pairs = key_atom_sdram_address[position_ka_pair];
        position_ka_pair += 1;

        // cycle through keys in this region looking for the key find atoms of
        for (uint32_t key_atom_pair_id = 0; key_atom_pair_id <
                n_key_atom_pairs; key_atom_pair_id++){
            uint32_t key_to_check =
                key_atom_sdram_address[position_ka_pair + SRC_BASE_KEY];

            // if key is correct, return atoms
            if (key_to_check == key){
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
    spin1_exit(0);
    return 0;
}

//! \brief gets data about the bitfields being considered
//! \param[in/out] keys: the data holder to populate
//! \param[in] mid_point: the point in the sorted bit fields to look for
//! \return the number of unique keys founds.
uint32_t population_master_pop_bit_field_ts(
        master_pop_bit_field_t * keys, uint32_t mid_point){

    uint32_t n_keys = 0;
    // check each bitfield to see if the key been recorded already
    for (uint32_t bit_field_index = 0; bit_field_index < mid_point;
            bit_field_index++){

        // get key
        uint32_t key = sorted_bit_fields[bit_field_index][BIT_FIELD_BASE_KEY];

        // start cycle looking for a clone
        uint32_t keys_index = 0;
        bool found = false;
        while(!found && keys_index < n_keys){
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
    table_t* table_cast = (table_t*) uncompressed_table_address;

    // flag for when found. no point starting move till after
    bool found = false;

    // iterate through all entries
    for(uint32_t entry_id=0; entry_id < table_cast->size; entry_id++){

        // if key matches, sort entry (assumes only 1 entry, otherwise boomed)
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
                table_cast->entries[entry_id - 1].route =
                    table_cast->entries[entry_id].route;
                table_cast->entries[entry_id - 1].source =
                    table_cast->entries[entry_id].source;
                table_cast->entries[entry_id - 1].key_mask.key =
                    table_cast->entries[entry_id].key_mask.key;
                table_cast->entries[entry_id - 1].key_mask.mask =
                    table_cast->entries[entry_id].key_mask.mask;
            }
        }
    }

    // update size by the removal of 1 entry
    table_cast->size -= 1;
}

//! \brief finds the processor id of a given bitfield address (search though
//! the bit field by processor
//! \param[in] bit_field_address: the location in sdram where the bitfield
//! starts
//! \return the processor id that this bitfield address is associated.
uint32_t locate_processor_id_from_bit_field_address(
        address_t bit_field_address){

    uint32_t n_pairs = user_register_content[REGION_ADDRESSES][N_PAIRS];
    for (uint32_t bf_by_proc = 0; bf_by_proc < n_pairs; bf_by_proc++){
        _bit_field_by_processor_t element = bit_field_by_processor[bf_by_proc];
        for (uint32_t addr_index = 0; addr_index < element.length_of_list;
                addr_index ++){
            if (element.bit_field_addresses[addr_index] == bit_field_address){
                return element.processor_id;
            }
        }
    }
    log_error(
        "failed to find the bitfield address %x anywhere.", bit_field_address);
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
    sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_FAIL;
    spin1_exit(0);
    return 0;
}

//! \brief sets a bitfield so that processors within the original route which
//! are not filterable, are added to the new route.
//! \param[in] processors: bitfield processors new route
//! \param[in] original_entry: the original router entry
//! \param[in] bit_field_processors: the processors which are filterable.
//! \param[in] n_bit_fields: the number of bitfields being assessed
void set_new_route_with_fixed_processors(
        bit_field_t processors, entry_t* original_entry,
        uint32_t * bit_field_processors, uint32_t n_bit_fields){

    // cast original entry route to a bitfield for ease of use
    bit_field_t original_route = (bit_field_t) &original_entry->route;

    // only set entries in the new route from the old route if the core has not
    // got a bitfield associated with it.
    for (uint32_t processor_id = 0; processor_id < MAX_PROCESSORS;
            processor_id++){
        // original route has this processor
        if (bit_field_test(
                original_route,
                (MAX_PROCESSORS - processor_id) + MAX_LINKS_PER_ROUTER)){

            // search through the bitfield processors to see if it exists
            bool found = false;
            for (uint32_t bit_field_index = 0; bit_field_index < n_bit_fields;
                    bit_field_index++){
                if(bit_field_processors[bit_field_index] == processor_id){
                    found = true;
                }
            }

            // if not a bitfield core, add to new route, as cant filter this
            // away.
            if (!found){
                bit_field_set(
                    processors,
                    (MAX_PROCESSORS - processor_id) + MAX_LINKS_PER_ROUTER);
            }
        }
    }
}

//! \brief generates the router table entries for the original entry in the
//! original routing table, where the new entries are atom level entries based
//! off the bitfields.
//! \param[in] addresses: the addresses in sdram where the bitfields exist
//! \param[in] n_bit_fields: the number of bitfields we are considering here
//! \param[in] original_entry: the original routing table entry that is being
//! expanded by the bitfields
//! \param[in] rt_address_ptr: the sdram address where the new atom level table
//! will be put once completed.
//! \return bool that states that if the atom routing table was generated or not
bool generate_entries_from_bitfields(
        address_t* addresses, uint32_t n_bit_fields, entry_t* original_entry,
        address_t* rt_address_ptr){

    // get processors by bitfield
    uint32_t * bit_field_processors = MALLOC(n_bit_fields * sizeof(uint32_t));
    if (bit_field_processors == NULL){
        log_error("failed to allocate memory for bitfield processors");
        return false;
    }

    // get the processor ids
    for(uint32_t bf_proc = 0; bf_proc < n_bit_fields; bf_proc++){
        bit_field_processors[bf_proc] =
            locate_processor_id_from_bit_field_address(addresses[bf_proc]);
    }

    // create sdram holder for the table we're going to generate
    uint32_t n_atoms = locate_key_atom_map(original_entry->key_mask.key);
    *rt_address_ptr = MALLOC_SDRAM(
        (uint) routing_table_sdram_size_of_table(n_atoms));

    if (*rt_address_ptr == NULL){
        FREE(bit_field_processors);
        log_error("can not allocate sdram for the sdram routing table");
        return false;
    }

    // update the tracker for the rt address
    table_t* sdram_table = (table_t*) *rt_address_ptr;

    // update the size of the router table, as we know there will be one entry
    // per atom
    sdram_table->size = n_atoms;

    // set up the new route process
    uint32_t size = get_bit_field_size(MAX_PROCESSORS + MAX_LINKS_PER_ROUTER);
    bit_field_t processors =
        bit_field_alloc(MAX_PROCESSORS + MAX_LINKS_PER_ROUTER);

    if (processors == NULL){
        log_error(
            "could not allocate memory for the processor tracker when "
            "making entries from bitfields");
        FREE(bit_field_processors);
        FREE(sdram_table);
        return false;
    }

    // iterate though each atom and set the route when needed
    for (uint32_t atom = 0; atom < n_atoms; atom++){

        // wipe history
        clear_bit_field(processors, size);

        // update the processors so that the fixed none filtered processors
        // are set
        set_new_route_with_fixed_processors(
            processors, original_entry, bit_field_processors, n_bit_fields);

        // iterate through the bitfield cores and see if they need this atom
        for (uint32_t bf_index = 0; bf_index < n_bit_fields; bf_index++){
            bool needed = bit_field_test(
                (bit_field_t) &addresses[bf_index][START_OF_BIT_FIELD_DATA],
                atom);
            if (needed){
                bit_field_set(processors, bit_field_processors[bf_index]);
            }
        }

        // get the entry and fill in details.
        entry_t* new_entry = &sdram_table->entries[atom];
        new_entry->key_mask.key = original_entry->key_mask.key + atom;
        new_entry->key_mask.mask = NEURON_LEVEL_MASK;
        new_entry->source = original_entry->source;
        sark_mem_cpy(
            &new_entry->route, &original_entry->route, sizeof(uint32_t));
    }

    FREE(bit_field_processors);
    FREE(processors);
    // do not remove sdram store, as that's critical to how this stuff works
    return true;

}

//! \brief counts how many cores are actually doing something.
//! \return the number of compressor cores doing something at the moment.
uint32_t count_many_on_going_compression_attempts_are_running(){
    uint32_t count = 0;
    for(uint32_t c_core_index = 0; c_core_index < n_compression_cores;
            c_core_index++){
        if (comp_core_mid_point[c_core_index] != DOING_NOWT){
            count ++;
        }
    }
    return count;
}

//! generates the routing table entries from this set of bitfields
//! \param[in] master_pop_key: the key to locate the bitfields for
//! \param[in] uncompressed_table: the location for the uncompressed table
//! \param[in] n_bfs_for_key: how many bitfields are needed for this key
//! \param[in] mid_point: the point where the search though sorted bit fields
//! ends.
//! \param[in] rt_address_ptr: the location in sdram to store the routing table
//! generated from the bitfields and original entry.
//! \return bool saying if it was successful or not
bool generate_rt_from_bit_field(
        uint32_t master_pop_key, address_t uncompressed_table,
        uint32_t n_bfs_for_key, uint32_t mid_point, address_t* rt_address_ptr){

    //for(uint32_t bf_index = 0; bf_index < n_bf_addresses; bf_index++){
    //    log_info(
    //        "bitfield address for sorted in index %d is %x",
    //        bf_index, sorted_bit_fields[bf_index]);
    //}

    // reduce future iterations, by finding the exact bitfield addresses
    address_t* addresses = MALLOC(n_bfs_for_key * sizeof(address_t));
    uint32_t index = 0;
    for (uint32_t bit_field_index = 0; bit_field_index < mid_point;
            bit_field_index++){
        if (sorted_bit_fields[bit_field_index][BIT_FIELD_BASE_KEY] ==
                master_pop_key){
            addresses[index] = sorted_bit_fields[bit_field_index];
            index += 1;
        }
    }

    // extract original routing entry from uncompressed table
    entry_t* original_entry = MALLOC(sizeof(entry_t));
    if (original_entry == NULL){
        log_error("can not allocate memory for the original entry.");
        FREE(addresses);
        return false;
    }

    extract_and_remove_entry_from_table(
        uncompressed_table, master_pop_key, original_entry);

    // create table entries with bitfields
    bool success = generate_entries_from_bitfields(
        addresses, n_bfs_for_key, original_entry, rt_address_ptr);
    if (!success){
        log_error(
            "can not create entries for key %d with %x bitfields.",
            master_pop_key, n_bfs_for_key);
        FREE(original_entry);
        FREE(addresses);
        return false;
    }

    FREE(original_entry);
    FREE(addresses);
    return true;
}

//! \brief clones the un compressed routing table, to another sdram location
//! \return: address of new clone, or null if it failed to clone
address_t clone_un_compressed_routing_table(){

    uncompressed_table_region_data_t* region =
        (uncompressed_table_region_data_t*) user_register_content[
            UNCOMP_ROUTER_TABLE];
    uint32_t sdram_used = routing_table_sdram_size_of_table(
        region->uncompressed_table.size);

    // allocate sdram for the clone
    address_t where_was_cloned = MALLOC_SDRAM(sdram_used);
    if (where_was_cloned == NULL){
        log_error("failed to allocate sdram for the cloned routing table for "
                  "uncompressed compression attempt");
        return NULL;
    }

    // copy over data
    sark_mem_cpy(
        where_was_cloned, &region->uncompressed_table.size, sdram_used);
    return where_was_cloned;
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
    master_pop_bit_field_t * keys = MALLOC(
        mid_point * sizeof(master_pop_bit_field_t));
    if (keys == NULL){
        log_error("cannot allocate memory for keys");
        return false;
    }

    // populate the master pop bit field
    *n_rt_addresses = population_master_pop_bit_field_ts(keys, mid_point);

    // add the uncompressed table, for allowing the bitfield table generator to
    // edit accordingly.
    *n_rt_addresses += 1;
    address_t uncompressed_table = clone_un_compressed_routing_table();
    if (uncompressed_table == NULL){
        log_error(
            "failed to clone uncompressed tables for attempt %d", mid_point);
        FREE(keys);
        return false;
    }

    bit_field_routing_tables = MALLOC(*n_rt_addresses * sizeof(address_t));
    if (bit_field_routing_tables == NULL){
        log_info("failed to allocate memory for bitfield routing tables");
        FREE(keys);
        return false;
    }

    // add clone to front of list, to ensure its easily accessible (plus its
    // part of the expected logic)

    bit_field_routing_tables[0] = uncompressed_table;

    // iterate through the keys, accumulating bitfields and turn into routing
    // table entries.
    for(uint32_t key_index = 1; key_index < *n_rt_addresses; key_index++){
        // holder for the rt address
        address_t rt_address;

        // create the routing table from the bitfield
        bool success = generate_rt_from_bit_field(
            keys[key_index -1].master_pop_key, uncompressed_table,
            keys[key_index - 1].n_bitfields_with_key, mid_point, &rt_address);

        // if failed, free stuff and tell above it failed
        if (!success){
            log_info("failed to allocate memory for rt table");
            FREE(keys);
            FREE(bit_field_routing_tables);
            return false;
        }

        // store the rt address for this master pop key
        bit_field_routing_tables[key_index] = rt_address;
    }

    // free stuff
    FREE(keys);
    return true;
}

//! \brief frees sdram from the compressor core.
//! \param[in] the compressor core to clear sdram usage from
//! \return bool stating that it was successful in clearing sdram
bool free_sdram_from_compression_attempt(uint32_t comp_core_index){
    uint32_t elements = comp_cores_bf_tables[comp_core_index].n_elements;
    log_debug("removing %d elements from index %d", elements, comp_core_index);
    for (uint32_t core_bit_field_id = 0; core_bit_field_id < elements;
            core_bit_field_id++){
        FREE(comp_cores_bf_tables[comp_core_index].elements[core_bit_field_id]);
    }
    FREE(comp_cores_bf_tables[comp_core_index].elements);
    comp_cores_bf_tables[comp_core_index].elements = NULL;
    return true;
}

//! \brief locate the core index for this processor id.
//! \param[in] processor_id: the processor id to find index for.
//! \return the index in the compressor cores for this processor id
uint32_t get_core_index_from_id(uint32_t processor_id){
    for(uint32_t comp_core_index = 0; comp_core_index < n_compression_cores;
            comp_core_index++){
        if(compressor_cores[comp_core_index] == processor_id){
            return comp_core_index;
        }
    }
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
    sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_FAIL;
    spin1_exit(0);
    return 0;
}

//! \brief selects a compression core's index that's not doing anything yet
//! \param[in] midpoint: the midpoint this compressor is going to explore
//! \return the compressor core index for this attempt.
uint32_t select_compressor_core_index(uint32_t midpoint){
    for(uint32_t comp_core_index = 0; comp_core_index < n_compression_cores;
            comp_core_index++){
        if (comp_core_mid_point[comp_core_index] == DOING_NOWT){

            comp_core_mid_point[comp_core_index] = midpoint;
            n_available_compression_cores -= 1;
            return comp_core_index;
        }
    }
    log_error("cant find a core to allocate to you");
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
    sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_FAIL;
    spin1_exit(0);
    return 0;  // needed for compiler warning to shut up
}

//! \brief stores the addresses for freeing when response code is sent
//! \param[in] n_rt_addresses: how many bit field addresses there are
//! \param[in] comp_core_index: the compressor core
//! \param[in] compressed_address: the addresses for the compressed routing
//! table
//! \return bool stating if stored or not
bool record_address_data_for_response_functionality(
        uint32_t n_rt_addresses, uint32_t comp_core_index,
        address_t compressed_address, uint32_t mid_point){

    //free previous if there is any
    log_debug("n rt a = %d index = %d", n_rt_addresses, comp_core_index);
    if (comp_cores_bf_tables[comp_core_index].elements != NULL){
        bool success = free_sdram_from_compression_attempt(comp_core_index);
        if (!success){
            log_error("failed to free compressor core elements.");
            return false;
        }
        FREE(comp_cores_bf_tables[comp_core_index].elements);
    }

    // allocate memory for the elements
    comp_cores_bf_tables[comp_core_index].elements = MALLOC(
        n_rt_addresses * sizeof(address_t));
    if (comp_cores_bf_tables[comp_core_index].elements == NULL){
        log_error("cannot allocate memory for sdram tracker of addresses");
        return false;
    }

    // store the elements. note need to copy over, as this is a central malloc
    // space for the routing tables.
    comp_cores_bf_tables[comp_core_index].n_elements = n_rt_addresses;
    comp_cores_bf_tables[comp_core_index].n_bit_fields = mid_point;
    comp_cores_bf_tables[comp_core_index].compressed_table = compressed_address;
    for (uint32_t rt_index =0; rt_index < n_rt_addresses; rt_index++){
        comp_cores_bf_tables[comp_core_index].elements[rt_index] =
            bit_field_routing_tables[rt_index];
    }
    return true;
}


//! \brief update the mc message to point at right direction
//! \param[in] comp_core_index: the compressor core id.
void update_mc_message(uint32_t comp_core_index){
    log_debug("chip id = %d", spin1_get_chip_id());
    my_msg.srce_addr = spin1_get_chip_id();
    my_msg.dest_addr = spin1_get_chip_id();
    my_msg.flags = REPLY_NOT_EXPECTED;
    log_debug("core id =  %d", spin1_get_id());
    my_msg.srce_port = (RANDOM_PORT << PORT_SHIFT) | spin1_get_core_id();
    log_debug("compressor core = %d", compressor_cores[comp_core_index]);
    my_msg.dest_port =
        (RANDOM_PORT << PORT_SHIFT) | compressor_cores[comp_core_index];
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
    log_debug("n packets = %d", total_packets);
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
    log_debug(
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

    log_debug(
        "message contains command code %d, n sdp packets till "
        "delivered %d, address for compressed %d, fake heap data "
        "address %d total n tables %d, n tables in packet %d",
        my_msg.data[COMMAND_CODE], data->n_sdp_packets_till_delivered,
        data->address_for_compressed, data->fake_heap_data,
        data->total_n_tables);
    for(uint32_t rt_id = 0; rt_id < n_addresses_this_message; rt_id++){
        log_debug("table address is %x", data->tables[rt_id]);
    }
    log_debug("message length = %d", my_msg.length);
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
    log_debug("message length = %d", my_msg.length);
}


//! \brief sends a SDP message to a compressor core to do compression with
//!  a number of bitfields
//! \param[in] n_rt_addresses: how many addresses the bitfields merged
//!  into
//! \param[in] mid_point: the mid point in the binary search
bool set_off_bit_field_compression(
        uint32_t n_rt_addresses, uint32_t mid_point){

    // select compressor core to execute this
    uint32_t comp_core_index = select_compressor_core_index(mid_point);

    // allocate space for the compressed routing entries if required
    address_t compressed_address =
        comp_cores_bf_tables[comp_core_index].compressed_table;
    if (comp_cores_bf_tables[comp_core_index].compressed_table == NULL){
        compressed_address = MALLOC_SDRAM(
            routing_table_sdram_size_of_table(TARGET_LENGTH));
        comp_cores_bf_tables[comp_core_index].compressed_table =
            compressed_address;
        if (compressed_address == NULL){
            log_error(
                "failed to allocate sdram for compressed routing entries");
            return false;
        }
    }

    // record addresses for response processing code
    bool suc = record_address_data_for_response_functionality(
        n_rt_addresses, comp_core_index, compressed_address, mid_point);
    if (!suc){
        log_error("failed to store the addresses for response functionality");
        return false;
    }

    // update sdp to right destination
    update_mc_message(comp_core_index);

    // deduce how many packets
    uint32_t total_packets = deduce_total_packets(n_rt_addresses);
    log_debug("total packets = %d", total_packets);

    // generate the packets and fire them to the compressor core
    uint32_t addresses_sent = 0;
    for (uint32_t packet_id =0; packet_id < total_packets; packet_id++){
        // if just one packet worth, set to left over addresses
        uint32_t n_addresses_this_message = deduce_elements_this_packet(
            packet_id, n_rt_addresses, addresses_sent);
        log_debug(
            "sending %d addresses this message", n_addresses_this_message);

        // set data components
        if (packet_id == 0){  // first packet
            set_up_first_packet(
                total_packets, compressed_address, n_rt_addresses,
                n_addresses_this_message);
            log_debug("finished setting up first packet");
        }
        else{  // extra packets
            log_debug("sending extra packet id = %d", packet_id);
            setup_extra_packet(n_addresses_this_message, addresses_sent);
        }

        // update location in addresses
        addresses_sent += n_addresses_this_message;

        // send sdp packet
        send_sdp_message();
    }

    return true;
}

//! builds tables and tries to set off a compressor core based off midpoint
//! \param[in] mid_point: the mid point to start at
//! \return bool fag if it fails for memory issues
bool create_tables_and_set_off_bit_compressor(uint32_t mid_point){
    uint32_t n_rt_addresses = 0;
    log_debug("started create bit field router tables");
    bool success = create_bit_field_router_tables(mid_point, &n_rt_addresses);
    log_debug("finished creating bit field router tables");

    // if successful, try setting off the bitfield compression
    if (success){
        success = set_off_bit_field_compression(n_rt_addresses, mid_point);

         // if successful, move to next search point.
         if (!success){
            log_debug("failed to set off bitfield compression");
            return false;
         }
         else{
            return true;
         }
    }

    log_debug("failed to create bitfield tables for midpoint %d", mid_point);
    return false;
}

//! \brief try running compression on just the uncompressed (attempt to check
//!     that without bitfields compression will work).
//! \return bool saying success or failure of the compression
bool start_binary_search(){

    // if there's only there's no available, but cores still attempting. just
    // return. it'll bounce back when a response is received
    if (n_available_compression_cores == 0 &&
            count_many_on_going_compression_attempts_are_running() > 0){
        log_debug(
            "not got any extra cores, but cores are running. so waiting "
            "for their responses");
        reading_bit_fields = false;
        return true;
    }

    // deduce how far to space these testers
    uint32_t hops_between_compression_cores =
        n_bf_addresses / n_available_compression_cores;
    uint32_t multiplier = 1;

    // safety check for floored to 0.
    if (hops_between_compression_cores == 0){
        hops_between_compression_cores = 1;
    }

    log_debug("n_bf_addresses is %d", n_bf_addresses);
    log_debug("n available compression cores is %d",
    n_available_compression_cores);
    log_debug("hops between attempts is %d", hops_between_compression_cores);

    bool failed_to_malloc = false;
    int new_mid_point = hops_between_compression_cores * multiplier;
    log_debug("n bf addresses = %d", n_bf_addresses);

    for (int index = 0; index < n_bf_addresses; index++){
        log_debug(
            "sorted bitfields address at index %d is %x",
            index, sorted_bit_fields[index]);
    }

    // iterate till either ran out of cores, or failed to malloc sdram during
    // the setup of a core or when gone too far
    while (n_available_compression_cores != 0 && !failed_to_malloc &&
            new_mid_point <= n_bf_addresses){

        log_info("next mid point to consider = %d", new_mid_point);
        bool success = create_tables_and_set_off_bit_compressor(new_mid_point);
        log_debug("success is %d", success);

        if(success){
            multiplier ++;
        }
        else{
            log_debug(
                "failed to malloc when setting up compressor with multiplier"
                " %d", multiplier);
            failed_to_malloc = true;
        }

        //update to next new mid point
        new_mid_point = hops_between_compression_cores * multiplier;
    }
    log_debug("finished the start of compression core allocation");
    
    // if it did not set off 1 compression. fail fully. coz it wont ever get
    // anything done. host will pick up the slack
    if (multiplier == 1){
        log_debug("failed at first bitfield");
        return false;
    }
    
    // set off at least one compression, but at some point failed to malloc 
    // sdram. assume this is the cap on how many cores can be ran at any 
    // given time
    if (failed_to_malloc){
        n_available_compression_cores = 0;
    }

    // return success for reading in and sorting bitfields
    reading_bit_fields = false;
    
    // say we've started
    return true;
}

//! sort out bitfields into processors and the keys of the bitfields to remove
//! \param[out] sorted_bf_by_processor: the sorted stuff
bool sort_sorted_to_cores(
        proc_bit_field_keys_t* sorted_bf_by_processor){
    sorted_bf_by_processor = MALLOC(
        user_register_content[REGION_ADDRESSES][N_PAIRS] *
        sizeof(proc_bit_field_keys_t));
    if (sorted_bf_by_processor == NULL){
        log_error(
            "failed to allocate memory for the sorting of bitfield to keys");
        return false;
    }

    //locate how many bitfields in the search space accepted that are of a
    // given core.
    uint position_in_region_data = START_OF_ADDRESSES_DATA;
    for (uint32_t r_id = 0;
            r_id < user_register_content[REGION_ADDRESSES][N_PAIRS];
            r_id++){

        // locate processor id for this region
        uint32_t region_proc_id = user_register_content[
            REGION_ADDRESSES][position_in_region_data + PROCESSOR_ID];
        sorted_bf_by_processor[r_id].processor_id = region_proc_id;

        // count entries
        uint32_t n_entries = 0;
        for(uint32_t bf_index = 0; bf_index < best_search_point; bf_index++){
            if (sorted_bit_fields_processor_ids[bf_index] == region_proc_id){
                n_entries ++;
            }
        }

        // update length
        sorted_bf_by_processor[r_id].length_of_list = n_entries;

        // alloc for keys
        sorted_bf_by_processor[r_id].master_pop_keys = MALLOC(
            n_entries * sizeof(uint32_t));
        if (sorted_bf_by_processor[r_id].master_pop_keys == NULL){
            log_error(
                "failed to allocate memory for the master pop keys for "
                "processor %d in the sorting of successful bitfields to "
                "remove.", region_proc_id);
            for (uint32_t free_id =0; free_id < r_id; free_id++){
                FREE(sorted_bf_by_processor->master_pop_keys);
            }
            FREE(sorted_bf_by_processor);
            return false;
        }

        // put keys in the array
        uint32_t array_index = 0;
        for(uint32_t bf_index = 0; bf_index < best_search_point; bf_index++){
            if (sorted_bit_fields_processor_ids[bf_index] == region_proc_id){
                sorted_bf_by_processor->master_pop_keys[array_index] =
                    sorted_bit_fields[bf_index][BIT_FIELD_BASE_KEY];
                array_index ++;
            }
        }
    }

    return true;
}

//! \brief finds the region id in the region addresses for this processor id
//! \param[in] processor_id: the processor id to find the region id in the
//! addresses
//! \return the address in the addresses region for the processor id
address_t find_processor_bit_field_region(uint32_t processor_id){

    // find the right bitfield region
    uint position_in_region_data = START_OF_ADDRESSES_DATA;
    for (uint32_t r_id = 0;
            r_id < user_register_content[REGION_ADDRESSES][N_PAIRS];
            r_id ++){
        uint32_t region_proc_id = user_register_content[
            REGION_ADDRESSES][position_in_region_data + PROCESSOR_ID];
        if (region_proc_id == processor_id){
            return (address_t) user_register_content[REGION_ADDRESSES][
                position_in_region_data + BITFIELD_REGION];
        }
        position_in_region_data += ADDRESS_PAIR_LENGTH;
    }

    // if not found
    log_error("failed to find the right region. WTF");
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
    sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_SWERR;
    spin1_exit(0);
    return NULL;
}

//! \brief checks if a key is in the set to be removed.
//! \param[in] sorted_bf_key_proc: the key store
//! \param[in] key: the key to locate a entry for
//! \return true if found, false otherwise
bool has_entry_in_sorted_keys(
        proc_bit_field_keys_t sorted_bf_key_proc, uint32_t key){
    for (uint32_t element_index = 0;
            element_index < sorted_bf_key_proc.length_of_list;
            element_index++){
        if(sorted_bf_key_proc.master_pop_keys[element_index] == key){
            return true;
        }
    }
    return false;
}

//! \brief removes the merged bitfields from the application cores bitfield
//!        regions
//! \return bool if was successful or not
bool remove_merged_bitfields_from_cores(){

    proc_bit_field_keys_t* sorted_bf_key_proc = NULL;

    // sort out the bitfields
    bool success = sort_sorted_to_cores(sorted_bf_key_proc);
    if (!success){
        log_error("could not sort out bitfields to keys.");
        return false;
    }

    // iterate though the cores sorted, and remove said bitfields from its
    // region
    for (uint32_t core_index = 0;
            core_index < user_register_content[REGION_ADDRESSES][N_PAIRS];
            core_index++){
        uint32_t proc_id = sorted_bf_key_proc[core_index].processor_id;
        address_t bit_field_region = find_processor_bit_field_region(proc_id);

        // iterate though the bitfield region looking for bitfields with
        // correct keys to remove
        uint32_t n_bit_fields = bit_field_region[N_BIT_FIELDS];
        bit_field_region[N_BIT_FIELDS] =
            n_bit_fields -  sorted_bf_key_proc[core_index].length_of_list;

        // pointers for shifting data up by excluding the ones been added to
        // router.
        uint32_t write_index = START_OF_BIT_FIELD_TOP_DATA;
        uint32_t read_index = START_OF_BIT_FIELD_TOP_DATA;

        // iterate though the bitfields only writing ones which are not removed
        for (uint32_t bf_index = 0; bf_index < n_bit_fields; bf_index++){
            uint32_t sdram_key = 
                bit_field_region[read_index + BIT_FIELD_BASE_KEY];

            // if entry is to be removed
            if(has_entry_in_sorted_keys(
                    sorted_bf_key_proc[core_index], sdram_key)){
                // hop over in reading, do no writing
                read_index += (
                    bit_field_region[read_index + BIT_FIELD_N_WORDS] +
                    START_OF_BIT_FIELD_DATA);
            }
            else{  // write the data in the current write positions
                uint32_t words_written_read = START_OF_BIT_FIELD_DATA;
                if (write_index != read_index){
                    // key and n words
                    bit_field_region[write_index + BIT_FIELD_BASE_KEY] =
                        bit_field_region[read_index + BIT_FIELD_BASE_KEY];
                    bit_field_region[write_index + BIT_FIELD_N_WORDS] =
                        bit_field_region[read_index + BIT_FIELD_N_WORDS];

                    // copy the bitfield over to the new location
                    sark_mem_cpy(
                        &bit_field_region[
                            read_index + START_OF_BIT_FIELD_DATA],
                        &bit_field_region[
                            write_index + START_OF_BIT_FIELD_DATA],
                        bit_field_region[read_index + BIT_FIELD_N_WORDS]);

                    words_written_read +=
                        bit_field_region[write_index + BIT_FIELD_N_WORDS];
                }

                // update pointers
                write_index += words_written_read;
                read_index += words_written_read;
            }
        }
    }

    // free items
    for (uint32_t core_index = 0;
            core_index < user_register_content[REGION_ADDRESSES][N_PAIRS];
            core_index++){
        if(sorted_bf_key_proc[core_index].length_of_list != 0){
            FREE(sorted_bf_key_proc[core_index].master_pop_keys);
        }
    }
    FREE(sorted_bf_key_proc);

    // return we successfully removed merged bitfields
    return true;
}

//! \brief tells ya if a compressor is already doing a mid point
//! \param[in] mid_point: the mid point to look for
//! \return bool saying true if there is a compressor running this right now
bool already_being_processed(int mid_point){
    for(uint32_t c_index = 0; c_index < n_compression_cores; c_index++){
        if (comp_core_mid_point[c_index] == mid_point){
            return true;
        }
    }
    return false;
}

//! \brief returns the best mid point tested to date. NOTE its only safe to call
//! this after the first attempt finished. which is acceptable
//! \return the best bf midpoint tested and success
int best_mid_point_to_date(){

    // go backwards to find the first passed value
    for (int n_bf = n_bf_addresses; n_bf >= 0; n_bf --){
        if (bit_field_test(mid_points_successes, n_bf)){
            log_debug("returning %d", n_bf);
            return n_bf;
        }
    }
    // not officially correct, but best place to start search from
    //if no other value has worked. and as the 0 fails will force a complete
    //failure. safe
    return 0;
}

//! \brief returns the next midpoint which has been tested
//! \return the next tested bf midpoint from midpoint
uint32_t next_tested_mid_point_from(uint32_t mid_point){
     for (int n_bf = mid_point + 1; n_bf < n_bf_addresses ; n_bf ++){
        if (bit_field_test(tested_mid_points, n_bf)){
            log_debug("returns %d", n_bf);
            return n_bf;
        }
    }
    return n_bf_addresses;
}

//! \brief return the spaces higher than me which could be tested
//! \param[in] point: the point to look from
//! \param[out] length: the length of the testing cores.
//! \param[out] found_best: bool flag saying if found the best point overall
//! \return bool stating if it was successful or not in memory alloc
int* find_spaces_high_than_point(
        int point, int* length, int next_tested_point, bool* found_best){

    log_debug("found best is %d", *found_best);

    // if the diff between the best tested and next tested is 1, then the
    // best is the overall best
    if (next_tested_point - point == 1 && bit_field_test(
            tested_mid_points, next_tested_point)){
        *found_best = true;
        return NULL;
    }

    // find how many values are being tested between best tested and next
    // tested
    *length = 1;

    log_debug("locate already tested");
    for (int n_bf = next_tested_point; n_bf >= point; n_bf--){
        if (already_being_processed(n_bf)){
            *length += 1;
        }
    }
    log_info("length is %d", *length);

    // malloc the spaces
    log_debug("size is %d", *length * sizeof(int));
    int* testing_cores = MALLOC(*length * sizeof(int));
    log_debug("malloc-ed");
    if (testing_cores == NULL){
        log_error(
            "failed to allocate memory for the locate next midpoint searcher");
        return NULL;
    }

    // populate list
    log_info("populate list");
    testing_cores[0] = point;
    log_info("testing cores index %d is %d", 0, point);
    uint32_t testing_core_index = 1;
    for (int n_bf = point; n_bf <= next_tested_point; n_bf ++){

        if (already_being_processed(n_bf)){
            testing_cores[testing_core_index] = n_bf;
            log_info("testing cores index %d is %d", testing_core_index, n_bf);
            testing_core_index += 1;
        }
    }

    // return success
    return testing_cores;

}

//! \brief locates the next valid midpoint which has not been tested or being
//! tested and has a chance of working/ improving the space
//! \param[out] bool flag to say found best
//! \return midpoint to search
bool locate_next_mid_point(bool* found_best, int* new_mid_point){
    // get base line to start searching for new locations to test
    int best_mp_to_date = best_mid_point_to_date();
    int next_tested_point = next_tested_mid_point_from(best_mp_to_date);
    int length = 0;

    log_debug(
        "next tested point from %d is %d",
        best_mp_to_date, next_tested_point);

    if (best_mp_to_date == next_tested_point){
        *found_best = true;
        best_search_point = best_mp_to_date;
        *new_mid_point = DOING_NOWT;
        log_debug("best search point is %d", best_mp_to_date);
        return true;
    }

    // fill in the locations bigger than best that are being tested
    log_debug("find spaces");
    int* higher_testers = find_spaces_high_than_point(
        best_mp_to_date, &length, next_tested_point, found_best);
    log_debug("populated higher testers");

    // exit if best found
    if (*found_best){
        log_debug("found best");
        best_search_point = best_mp_to_date;
        return true;
    }
    log_debug("passed test");


    // failed to find next point due to malloc issues
    if (higher_testers == NULL){
        log_error("failed to find spaces higher than point");
        return false;
    }

    // got spaces, find one with the biggest difference
    log_debug("looking for biggest dif with length %d", length);
    int biggest_dif = 0;
    for (int test_base_index = 0; test_base_index < length - 1;
            test_base_index++){

        // will be going from low to high, for that's how its been searched
        int diff = higher_testers[test_base_index + 1] -
            higher_testers[test_base_index];
        log_debug("diff is %d", diff);
        if (diff > biggest_dif){
            biggest_dif = diff;
        }
    }
    log_debug("best dif is %d", biggest_dif);

    // handle case of no split between best and last tested
    // NOTE this only happens with n compression cores of 1.
    if (length == 1){
        log_info(
            "next tested point = %d, best_mp_to_date = %d",
            next_tested_point, best_mp_to_date);
        int hop = (next_tested_point - best_mp_to_date) / 2;
        if (hop == 0){
            hop = 1;
        }
        *new_mid_point = best_mp_to_date + hop;
        log_info("new midpoint is %d", *new_mid_point);
        return true;
    }

    // locate the first with biggest dif, split in middle and return that as
    // new mid point to test
    log_info("cycling");
    for (int test_base_index = 0; test_base_index < length; test_base_index++){
        log_debug("entered");

        // will be going from high to low, for that's how its been searched
        int diff = higher_testers[test_base_index + 1] -
            higher_testers[test_base_index];
        log_debug("located diff %d, looking for b diff %d", diff, biggest_dif);

        // if the right diff, figure the midpoint of these points.
        if (diff == biggest_dif){
            // deduce hop
            int hop = (biggest_dif / 2);
            log_debug("hop is %d", hop);
            if (hop == 0){
                hop = 1;
            }

            // deduce new mid point
            *new_mid_point = higher_testers[test_base_index] + hop;
            log_info("next mid point to test is %d", *new_mid_point);

            // check if we're testing this already, coz if we are. do nowt
            if (already_being_processed(*new_mid_point)){
                log_info(
                    "already testing mid point %d, so do nothing",
                    *new_mid_point);
                *new_mid_point = DOING_NOWT;
                return true;
            }

            // if hitting the bottom. check that uncompressed worked or not
            if (*new_mid_point == 0){
                // check that it worked (it might not have finished, in some
                // odd flow
                if (bit_field_test(mid_points_successes, *new_mid_point)){
                    best_search_point = *new_mid_point;
                    *found_best = true;
                    return true;
                }
                // if we got here its odd. but put this here for completeness
                if(bit_field_test(tested_mid_points, *new_mid_point)){
                    log_error(
                        "got to the point of searching for mid point 0."
                        " And 0 has been tested and failed. therefore complete"
                        " failure has occurred.");
                    return false;
                }
            }
        }
    }
    log_info("left cycle");
    FREE(higher_testers);
    return true;
}

//! \brief compress the bitfields from the best location
void carry_on_binary_search(uint unused0, uint unused1){
    // api requirement
    use(unused0);
    use(unused1);
    log_info("started carry on");

    bool failed_to_malloc = false;
    bool found_best = false;
    bool nothing_to_do = false;

    log_debug("found best is %d", found_best);

    // iterate till either ran out of cores, or failed to malloc sdram during
    // the setup of a core or found best or no other mid points need to be
    // tested
    log_debug("start while");
    while (n_available_compression_cores != 0 && !failed_to_malloc &&
            !found_best && !nothing_to_do){

        log_debug("try a carry on core");

        // locate next midpoint to test
        int mid_point;
        bool success = locate_next_mid_point(&found_best, &mid_point);

        // check for not needing to do things but wait
        if (mid_point == DOING_NOWT && !found_best){
            log_info("no need to cycle, as nowt to do but wait");
            nothing_to_do = true;
        }
        else{
            // if finished search, load best into table
            if (found_best){
                log_info(
                    "finished search successfully best mid point was %d",
                    best_search_point);
                load_routing_table_into_router();
                log_debug("finished loading table");
                vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
                sark_virtual_processor_info[spin1_get_core_id()].user1 =
                    EXITED_CLEANLY;
                spin1_exit(0);
                return;
            }
            else{
                // not found best, so try to set off compression if memory done

                log_debug("trying with midpoint %d", mid_point);
                if (!success){
                    failed_to_malloc = true;
                }
                else{  // try a compression run
                    success = create_tables_and_set_off_bit_compressor(
                        mid_point);

                    // failed to set off the run for a memory reason
                    if (!success){
                        failed_to_malloc = true;
                    }
                }
            }
        }
    }

    log_debug("checking state");

    // if failed to malloc, limit exploration to the number of cores running.
    if (failed_to_malloc){
        n_available_compression_cores = 0;

        // if the current running number of cores is 0, then we cant generate
        // the next midpoint,
        if(count_many_on_going_compression_attempts_are_running() == 0){
            uint32_t best_mid_point_tested = best_mid_point_to_date();

            // check if current reach is enough to count as a success
            if ((n_bf_addresses / best_mid_point_tested) >=
                    user_register_content[REGION_ADDRESSES][THRESHOLD]){
                found_best = true;
                best_search_point = best_mid_point_tested;
                log_debug("finished search by end user QoS");
                load_routing_table_into_router();
            }
            else{
                log_error(
                    "failed to compress enough bitfields for threshold.");
                vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
                sark_virtual_processor_info[spin1_get_core_id()].user1 =
                    EXIT_FAIL;
                spin1_exit(0);
            }
        }
    }

    // set flag for handling responses to bounce back in here
    still_trying_to_carry_on = false;
}

//! \brief processes the response from the compressor attempt
//! \param[in] comp_core_index: the compressor core id
//! \param[in] the response code / finished state
void process_compressor_response(
        uint32_t comp_core_index, uint32_t finished_state){
    
    // filter off finished state
    if (finished_state == SUCCESSFUL_COMPRESSION){
        log_info(
            "successful from core %d doing mid point %d",
            compressor_cores[comp_core_index],
            comp_core_mid_point[comp_core_index]);
        bit_field_set(tested_mid_points, comp_core_mid_point[comp_core_index]);
        bit_field_set(
            mid_points_successes, comp_core_mid_point[comp_core_index]);

        // set tracker if its the best seen so far
        if (best_mid_point_to_date() == comp_core_mid_point[comp_core_index]){
            best_search_point = comp_core_mid_point[comp_core_index];
            sark_mem_cpy(
                last_compressed_table,
                comp_cores_bf_tables[comp_core_index].compressed_table,
                routing_table_sdram_size_of_table(TARGET_LENGTH));
        }

        // release for next set
        comp_core_mid_point[comp_core_index] = DOING_NOWT;
        n_available_compression_cores ++;

        // kill any search below this point, as they all successful if this one
        // was / redundant as this is a better search.

        // free the sdram associated with this compressor core.
        bool success = free_sdram_from_compression_attempt(comp_core_index);
        if (!success){
            log_error("failed to free sdram for compressor core %d. WTF",
                      comp_core_index);
        }
        log_debug("finished process of successful compression");
    }
    else if (finished_state == FAILED_MALLOC){
        log_debug(
            "failed to malloc from core %d doing mid point %d",
            comp_core_index, comp_core_mid_point[comp_core_index]);
        // this will threshold the number of compressor cores that
        // can be ran at any given time.
        comp_core_mid_point[comp_core_index] = DOING_NOWT;
        // free the sdram associated with this compressor core.
        bool success = free_sdram_from_compression_attempt(comp_core_index);
        if (!success){
            log_error("failed to free sdram for compressor core %d. WTF",
                      comp_core_index);
        }
    }
    else if (finished_state == FAILED_TO_COMPRESS){
        log_debug(
            "failed to compress from core %d doing mid point %d",
            comp_core_index, comp_core_mid_point[comp_core_index]);

        // it failed to compress, so it was successful in malloc.
        // so mark the midpoint as tested, and free the core for another
        // attempt
        bit_field_set(tested_mid_points, comp_core_mid_point[comp_core_index]);
        int compression_mid_point = comp_core_mid_point[comp_core_index];
        comp_core_mid_point[comp_core_index] = DOING_NOWT;
        n_available_compression_cores ++;
    
        // set all indices above this one to false, as this one failed
        for(int test_index = compression_mid_point;
                test_index < n_bf_addresses; test_index++){
            bit_field_set(tested_mid_points, test_index);
        }
    
        // tell all compression cores trying midpoints above this one
        // to stop, as its highly likely a waste of time.
        for (uint32_t check_core_id = 0;
                check_core_id < n_compression_cores; check_core_id++){
            if (comp_core_mid_point[check_core_id] > compression_mid_point){
                send_sdp_force_stop_message(check_core_id);
            }
        }

        // free the sdram associated with this compressor core.
        bool success = free_sdram_from_compression_attempt(comp_core_index);
        if (!success){
            log_error("failed to free sdram for compressor core %d. WTF",
                      comp_core_index);
        }
    }
    else if (finished_state == RAN_OUT_OF_TIME){
        log_debug(
            "failed by time from core %d doing mid point %d",
            comp_core_index, comp_core_mid_point[comp_core_index]);

        // if failed to compress by the end user considered QoS. So it
        // was successful in malloc. So mark the midpoint as tested,
        // and free the core for another attempt
        bit_field_set(tested_mid_points, comp_core_mid_point[comp_core_index]);
        comp_core_mid_point[comp_core_index] = DOING_NOWT;
        n_available_compression_cores ++;

        // free the sdram associated with this compressor core.
        bool success = free_sdram_from_compression_attempt(comp_core_index);
        if (!success){
            log_error("failed to free sdram for compressor core %d. WTF",
                      comp_core_index);
        }
    }
    else if (finished_state == FORCED_BY_COMPRESSOR_CONTROL){
        log_debug(
            "ack from forced from core %d doing mid point %d",
            comp_core_index, comp_core_mid_point[comp_core_index]);
        // this gives no context of why the control killed it. just
        // free the core for another attempt
        comp_core_mid_point[comp_core_index] = DOING_NOWT;
        n_available_compression_cores ++;

        // free the sdram associated with this compressor core.
        bool success = free_sdram_from_compression_attempt(comp_core_index);
        if (!success){
            log_error("failed to free sdram for compressor core %d. WTF",
                      comp_core_index);
        }
    }
    else{
        log_error("no idea what to do with finished state %d, from "
                  "core %d ignoring", finished_state, comp_core_index);
    }

    // having processed the packet, and there are spare cores for compression
    // attempts, try to set off another search.  (this encapsulates the
    // finish state as well.
    log_debug(
        "n av cores = %d, bool of reading is %d",
        n_available_compression_cores, reading_bit_fields);
    if (n_available_compression_cores > 0 && !reading_bit_fields){
        if (!still_trying_to_carry_on){
            log_info("setting off carry on");
            still_trying_to_carry_on = true;
            spin1_schedule_callback(
                carry_on_binary_search, 0, 0, COMPRESSION_START_PRIORITY);
        }else{
            log_info("all ready in carry on mode. ignoring");
        }
    }
    else{
        log_info("not ready to carry on yet");
    }
}

//! \brief the sdp control entrance.
//! \param[in] mailbox: the message
//! \param[in] port: don't care.
void sdp_handler(uint mailbox, uint port) {
    use(port);

    log_debug("received response");

    // get data from the sdp message
    sdp_msg_pure_data *msg = (sdp_msg_pure_data *) mailbox;
    log_debug("command code is %d", msg->data[COMMAND_CODE]);
    log_debug(
        "response code was %d", msg->data[START_OF_SPECIFIC_MESSAGE_DATA]);

    // filter off the port we've decided to use for this
    if (msg->srce_port >> PORT_SHIFT == RANDOM_PORT){
        log_debug("correct port");
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
            log_debug("response packet");
            uint32_t comp_core_index = get_core_index_from_id(
                (msg->srce_port & CPU_MASK));

            // response code just has one value, so being lazy and not casting
            uint32_t finished_state = msg->data[START_OF_SPECIFIC_MESSAGE_DATA];

            // free message now, nothing left in it
            sark_msg_free((sdp_msg_t*) msg);
            
            process_compressor_response(comp_core_index, finished_state);
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

    log_debug("finish sdp process");
}

//! \brief reads a bitfield and deduces how many bits are not set
//! \param[in] bit_field_struct: the location of the bitfield
//! \return how many redundant packets there are
uint32_t detect_redundant_packet_count(address_t bit_field_struct){
    //log_info("address's location is %d", bit_field_struct);
    //log_info(" key is %d", bit_field_struct[BIT_FIELD_BASE_KEY]);
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
    //log_info("n filtered packets = %d", n_filtered_packets);
    return n_filtered_packets;
}

//! \brief do some location and addition stuff
//! \param[in] coverage:the set of bitfields and corresponding processors
//!                      for bitfields with a given redundant packet count.
//! \param[in] coverage_index: where in the coverage array we are
//! \param[in] cores_to_add_for: the cores who's bitfields we want to find
//! \param[in] cores_to_add_length: length of array of core ids
//! \param[in] diff: the amount of bitfields to add for these cores
//! \param[out] covered: the new set of bitfields
//! \return the new covered level
uint32_t locate_and_add_bit_fields(
        coverage_t** coverage, uint32_t coverage_index,
        uint32_t *cores_to_add_for, uint32_t cores_to_add_length, uint32_t diff,
        uint32_t covered){

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
                    log_debug(
                        "removing from indexs %d, %d",
                        coverage_index, processor_to_check_index);

                    log_debug(
                        "dumping into sorted at index %d address %x and is %x",
                        sorted_bit_field_current_fill_loc,
                        coverage[coverage_index]->bit_field_addresses[
                            processor_to_check_index],
                        sorted_bit_fields[sorted_bit_field_current_fill_loc]);
                }
            }
        }
    }


    return covered;
}

//! \brief orders the bitfields for the binary search based off the impact
//! made in reducing the redundant packet processing on cores.
//! \param[in] coverage: the set of bitfields and corresponding processors
//!                      for bitfields with a given redundant packet count.
//! \param[in] proc_cov_by_bit_field: the processors bitfield redundant
//! packet counts.
//! \param[in] n_pairs: the number of processors/elements to search
//! \param[in] n_unique_redundant_packet_counts: the count of how many unique
//!      redundant packet counts there are.
//! \return None
void order_bit_fields_based_on_impact(
        coverage_t** coverage, _proc_cov_by_bitfield_t** proc_cov_by_bit_field,
        uint32_t n_pairs, uint32_t n_unique_redundant_packet_counts){

    // sort processor coverage by bitfield so that ones with longest length are
    // at the front of the list
    sort_by_n_bit_fields(proc_cov_by_bit_field, n_pairs);

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
        log_info(
            "adding core %d into the search",
            proc_cov_by_bit_field[worst_core_id]->processor_id);

        // determine difference between the worst and next worst
        uint32_t diff = proc_cov_by_bit_field[worst_core_id]->length_of_list -
             proc_cov_by_bit_field[worst_core_id + 1]->length_of_list;
        log_info("diff is %d", diff);

        // sort by bubble sort so that the most redundant packet count
        // addresses are at the front
        sort_by_redundant_packet_count(
            proc_cov_by_bit_field, n_pairs, worst_core_id);

        // print for sanity
        for(uint32_t r_packet_index = 0;
                r_packet_index < proc_cov_by_bit_field[
                    worst_core_id]->length_of_list;
                r_packet_index ++){
            log_debug(
                "order of redundant packet count at index %d is %d",
                proc_cov_by_bit_field[worst_core_id]->redundant_packets[
                    r_packet_index]);
        }

        // print all coverage for sanity purposes
        for (uint32_t coverage_index = 0;
                coverage_index < n_unique_redundant_packet_counts;
                coverage_index++){
            for(uint32_t bit_field_index = 0;
                    bit_field_index < coverage[coverage_index]->length_of_list;
                    bit_field_index ++){
                log_debug(
                    "bitfield address in coverage at index %d in array index"
                     "%d is %x", coverage_index, bit_field_index,
                     coverage[coverage_index]->bit_field_addresses[
                        bit_field_index]);
            }
        }

        for (uint32_t coverage_index = 0;
                coverage_index < n_unique_redundant_packet_counts;
                coverage_index++){
            for(uint32_t bit_field_index = 0;
                    bit_field_index < coverage[coverage_index]->length_of_list;
                    bit_field_index ++){
                log_debug(
                    "bitfield proc in coverage at index %d in array index"
                     "%d is %x", coverage_index, bit_field_index,
                     coverage[coverage_index]->processor_ids[bit_field_index]);
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

            // print all coverage for sanity purposes
            /**for (uint32_t coverage_index = 0;
                    coverage_index < n_unique_redundant_packet_counts;
                    coverage_index++){
                for(uint32_t bit_field_index = 0;
                        bit_field_index < coverage[
                            coverage_index]->length_of_list;
                        bit_field_index ++){
                    log_info(
                        "bitfield address in coverage at index %d in array "
                        "index %d is %x", coverage_index, bit_field_index,
                         coverage[coverage_index]->bit_field_addresses[
                            bit_field_index]);
                }
            }

            for (uint32_t coverage_index = 0;
                    coverage_index < n_unique_redundant_packet_counts;
                    coverage_index++){
                for(uint32_t bit_field_index = 0;
                        bit_field_index < coverage[
                            coverage_index]->length_of_list;
                        bit_field_index ++){
                    log_info(
                        "bitfield proc in coverage after a move to sorted at "
                        "index %d in array index %d is %x", coverage_index,
                        bit_field_index,
                        coverage[coverage_index]->processor_ids[
                            bit_field_index]);
                }
            }
            log_info("next cycle of moving to sorted");*/
        }
    }



    // sort bitfields by coverage by n_redundant_packets so biggest at front
    sort_bitfields_so_most_impact_at_front(
        coverage, n_unique_redundant_packet_counts);

    // iterate through the coverage and add any that are left over.
    for (uint index = 0; index < n_unique_redundant_packet_counts;
            index ++){
        for (uint32_t bit_field_index = 0;
                bit_field_index < coverage[index]->length_of_list;
                bit_field_index++){
            if (coverage[index]->bit_field_addresses[bit_field_index] != NULL){

                sorted_bit_fields[sorted_bit_field_current_fill_loc] =
                        coverage[index]->bit_field_addresses[bit_field_index];

                //log_info(
                //    "dumping into sorted at index %d address %x and is %x",
                //    sorted_bit_field_current_fill_loc,
                //    coverage[index]->bit_field_addresses[bit_field_index],
                //    sorted_bit_fields[sorted_bit_field_current_fill_loc]);

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
    log_info("start cloning of uncompressed table");
    address_t sdram_clone_of_routing_table =
        clone_un_compressed_routing_table();
    if (sdram_clone_of_routing_table == NULL){
        log_error("could not allocate memory for uncompressed table for no "
                  "bit field compression attempt.");
        return false;
    }
    log_info("finished cloning of uncompressed table");

    // set up the bitfield routing tables so that it'll map down below
    log_info("allocating bf routing tables");
    bit_field_routing_tables = MALLOC(sizeof(address_t*));
    log_info("malloc finished");
    if (bit_field_routing_tables == NULL){
        log_error(
            "failed to allocate memory for the bit_field_routing tables");
        return false;
    }
    log_info("allocate to array");
    bit_field_routing_tables[0] = sdram_clone_of_routing_table;
    log_info("allocated bf routing tables");

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
    log_debug("n pairs of addresses = %d", n_pairs_of_addresses);

    // malloc the bt fields by processor
    bit_field_by_processor = MALLOC(
        n_pairs_of_addresses * sizeof(_bit_field_by_processor_t));
    if (bit_field_by_processor == NULL){
        log_error("failed to allocate memory for pairs, if it fails here. "
                  "might as well give up");
        return false;
    }
    
    // build processor coverage by bitfield
    _proc_cov_by_bitfield_t** proc_cov_by_bf = MALLOC(
        n_pairs_of_addresses * sizeof(_proc_cov_by_bitfield_t*));
    if (proc_cov_by_bf == NULL){
        log_error("failed to allocate memory for processor coverage by "
                  "bitfield, if it fails here. might as well give up");
        return false;
    }
    log_debug("finished malloc proc_cov_by_bf");

    // iterate through a processors bitfield region and get n bitfields
    for (uint r_id = 0; r_id < n_pairs_of_addresses; r_id++){
        
        // malloc for n redundant packets
        proc_cov_by_bf[r_id] = MALLOC(sizeof(
            _proc_cov_by_bitfield_t));
        if (proc_cov_by_bf[r_id] == NULL){
            log_error("failed to allocate memory for processor coverage for "
                      "region %d. might as well give up", r_id);
            return false;
        }

        // track processor id
        bit_field_by_processor[r_id].processor_id =
            user_register_content[REGION_ADDRESSES][
                position_in_region_data + PROCESSOR_ID];
        proc_cov_by_bf[r_id]->processor_id =
            user_register_content[REGION_ADDRESSES][
                position_in_region_data + PROCESSOR_ID];
        log_debug(
            "bit_field_by_processor in region %d processor id = %d",
            r_id, bit_field_by_processor[r_id].processor_id);

        // locate data for malloc memory calcs
        address_t bit_field_address = (address_t) user_register_content[
            REGION_ADDRESSES][position_in_region_data + BITFIELD_REGION];
        log_debug("bit_field_region = %x", bit_field_address);
        position_in_region_data += ADDRESS_PAIR_LENGTH;

        log_debug(
            "safety check. bit_field key is %d",
             bit_field_address[BIT_FIELD_BASE_KEY]);
        uint32_t pos_in_bitfield_region = N_BIT_FIELDS;
        uint32_t core_n_bit_fields = bit_field_address[pos_in_bitfield_region];
        log_debug("there are %d core bit fields", core_n_bit_fields);
        pos_in_bitfield_region = START_OF_BIT_FIELD_TOP_DATA;
        n_bf_addresses += core_n_bit_fields;
        
        // track lengths
        proc_cov_by_bf[r_id]->length_of_list = core_n_bit_fields;
        bit_field_by_processor[r_id].length_of_list = core_n_bit_fields;
        log_debug(
            "bit field by processor with region %d, has length of %d",
            r_id, core_n_bit_fields);
        
        // malloc for bitfield region addresses
        bit_field_by_processor[r_id].bit_field_addresses = MALLOC(
            core_n_bit_fields * sizeof(address_t));
        if (bit_field_by_processor[r_id].bit_field_addresses == NULL){
            log_error("failed to allocate memory for bitfield addresses for "
                      "region %d, might as well fail", r_id);
            return false; 
        }
        
        // malloc for n redundant packets
        proc_cov_by_bf[r_id]->redundant_packets = MALLOC(
            core_n_bit_fields * sizeof(uint));
        if (proc_cov_by_bf[r_id]->redundant_packets == NULL){
            log_error("failed to allocate memory for processor coverage for "
                      "region %d, might as well fail", r_id);
            return false;
        }

        // populate tables: 1 for addresses where each bitfield component starts
        //                  2 n redundant packets
        for (uint32_t bit_field_id = 0; bit_field_id < core_n_bit_fields;
                bit_field_id++){
            bit_field_by_processor[r_id].bit_field_addresses[
                bit_field_id] =
                    (address_t) &bit_field_address[pos_in_bitfield_region];
            log_debug(
                "bitfield at region %d at index %d is at address %x",
                r_id, bit_field_id,
                bit_field_by_processor[r_id].bit_field_addresses[
                    bit_field_id]);

            uint32_t n_redundant_packets =
                detect_redundant_packet_count(
                    (address_t) &bit_field_address[pos_in_bitfield_region]);
            proc_cov_by_bf[r_id]->redundant_packets[bit_field_id] =
                n_redundant_packets;
            log_debug(
                "prov cov by bitfield for region %d, redundant packets "
                "at index %d, has n redundant packets of %d",
                r_id, bit_field_id, n_redundant_packets);
            
            pos_in_bitfield_region += 
                START_OF_BIT_FIELD_DATA + bit_field_address[
                    pos_in_bitfield_region + BIT_FIELD_N_WORDS];
        }
    }

    // sort out teh searcher bitfields. as now first time where can do so
    // NOTE: by doing it here, the response from the uncompressed can be
    // handled correctly.
    log_debug("setting up search bitfields");
    bool success = set_up_search_bitfields();
    if (!success){
        log_error("can not allocate memory for search fields.");
        return false;
    }
    log_debug("finish setting up search bitfields");

    // set off a none bitfield compression attempt, to pipe line work
    log_info("sets off the uncompressed version of the search");
    set_off_no_bit_field_compression();

    // populate the bitfield by coverage
    log_info("n bitfield addresses = %d", n_bf_addresses);
    sorted_bit_fields = MALLOC(n_bf_addresses * sizeof(address_t));
    if(sorted_bit_fields == NULL){
        log_error("cannot allocate memory for the sorted bitfield addresses");
        return false;
    }

    sorted_bit_fields_processor_ids =
        MALLOC(n_bf_addresses * sizeof(uint32_t));
    if (sorted_bit_fields_processor_ids == NULL){
        log_error("cannot allocate memory for the sorted bitfields with "
                  "processors ids");
        return false;
    }

    uint length_n_redundant_packets = 0;
    uint * redundant_packets = MALLOC(n_bf_addresses * sizeof(uint));

    // filter out duplicates in the n redundant packets
    position_in_region_data = START_OF_ADDRESSES_DATA;
    for (uint r_id = 0; r_id < n_pairs_of_addresses; r_id++){
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
            uint x_packets = proc_cov_by_bf[
                r_id]->redundant_packets[bit_field_id];
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
    log_debug("length of n redundant packets = %d", length_n_redundant_packets);

    // malloc space for the bitfield by coverage map
    coverage_t** coverage = MALLOC(
        length_n_redundant_packets * sizeof(coverage_t*));
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
        log_debug(
            "try to allocate memory of size %d for coverage at index %d",
             sizeof(coverage_t), r_packet_index);
        coverage[r_packet_index] = MALLOC(sizeof(coverage_t));
        if (coverage[r_packet_index] == NULL){
            log_error(
                "failed to malloc memory for the bitfields by coverage "
                "for index %d. might as well fail", r_packet_index);
            return false;
        }
        
        // update the redundant packet pointer
        coverage[r_packet_index]->n_redundant_packets = 
            redundant_packets[r_packet_index];
        
        // search to see how long the list is going to be.
        uint32_t n_bf_with_same_r_packets = 0;
        for (uint r_id = 0; r_id < n_pairs_of_addresses; r_id++){
            uint length = proc_cov_by_bf[r_id]->length_of_list;
            for(uint red_packet_index = 0; red_packet_index < length;
                    red_packet_index ++){
                if(proc_cov_by_bf[r_id]->redundant_packets[
                        red_packet_index] == redundant_packets[r_packet_index]){
                    n_bf_with_same_r_packets += 1;
                }
            }
        }
        
        // update length of list
        coverage[r_packet_index]->length_of_list = n_bf_with_same_r_packets;
        
        // malloc list size for these addresses of bitfields with same 
        // redundant packet counts.
        coverage[r_packet_index]->bit_field_addresses = MALLOC(
            n_bf_with_same_r_packets * sizeof(address_t));
        if(coverage[r_packet_index]->bit_field_addresses == NULL){
            log_error(
                "failed to allocate memory for the coverage on index %d"
                " for addresses. might as well fail.", r_packet_index);
            return false;
        }
        
        // malloc list size for the corresponding processors ids for the 
        // bitfields
        log_debug(
            "trying to allocate %d bytes, for x bitfields same xr packets %d",
            n_bf_with_same_r_packets * sizeof(uint32_t),
            n_bf_with_same_r_packets);
        coverage[r_packet_index]->processor_ids = MALLOC(
            n_bf_with_same_r_packets * sizeof(uint32_t));
        if(coverage[r_packet_index]->processor_ids == NULL){
            log_error(
                "failed to allocate memory for the coverage on index %d"
                " for processors. might as well fail.", r_packet_index);
            return false;
        }
            
        // populate list of bitfields addresses which have same redundant 
        //packet count.
        log_debug(
            "populating list of bitfield addresses with same packet count");
        uint32_t processor_id_index = 0;
        for (uint r_id = 0; r_id < n_pairs_of_addresses; r_id++){
            for(uint red_packet_index = 0; 
                    red_packet_index < proc_cov_by_bf[r_id]->length_of_list;
                    red_packet_index ++){
                if(proc_cov_by_bf[r_id]->redundant_packets[red_packet_index] ==
                        redundant_packets[r_packet_index]){
                    log_debug(
                        "found! at %x",
                        bit_field_by_processor[ r_id].bit_field_addresses[
                            red_packet_index]);

                    coverage[r_packet_index]->bit_field_addresses[
                        processor_id_index] = bit_field_by_processor[
                            r_id].bit_field_addresses[red_packet_index];
                            
                    coverage[r_packet_index]->processor_ids[processor_id_index]
                        = bit_field_by_processor[r_id].processor_id;
                        
                    processor_id_index += 1;
                }
            }
        }
        //log_info(
        //    "processor id index = %d and need to fill in %d elements",
        //    processor_id_index, n_bf_with_same_r_packets);
    }

    // free the redundant packet tracker, as now tailored ones are in the dict
    FREE(redundant_packets);

    // order the bitfields based off the impact to cores redundant packet
    // processing
    order_bit_fields_based_on_impact(
        coverage, proc_cov_by_bf, n_pairs_of_addresses,
        length_n_redundant_packets);

    // free the data holders we don't care about now that we've got our
    // sorted bitfields list
    for(uint r_id = 0; r_id < n_pairs_of_addresses; r_id++){
        coverage_t* cov_element = coverage[r_id];
        FREE(cov_element->bit_field_addresses);
        FREE(cov_element->processor_ids);
        FREE(cov_element);
        _proc_cov_by_bitfield_t* proc_cov_element =
            proc_cov_by_bf[r_id];
        FREE(proc_cov_element->redundant_packets);
        FREE(proc_cov_element);
    }
    FREE(coverage);
    FREE(proc_cov_by_bf);

    for(int bf_index = 0; bf_index < n_bf_addresses; bf_index++){
        log_debug(
            "bitfield address for sorted in index %d is %x",
            bf_index, sorted_bit_fields[bf_index]);
    }

    return true; 
}

//! \brief starts the work for the compression search
void start_compression_process(uint unused0, uint unused1){
    //api requirements
    use(unused0);
    use(unused1);

    // will use this many palces. so exrtact at top
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;

    log_info("read in bitfields");
    bool success_reading_in_bit_fields = read_in_bit_fields();
    log_info("finished reading in bitfields");

    if (! success_reading_in_bit_fields){
        log_error("failed to read in bitfields, failing");
        sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_MALLOC;
        spin1_exit(0);
    }

    log_info("starting the binary search");
    bool success_start_binary_search = start_binary_search();
    log_info("finish starting of the binary search");

    if (!success_start_binary_search){
        log_error("failed to compress the routing table at all. Failing");
        sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_FAIL;
        spin1_exit(0);
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
    uncompressed_table_region_data_t* uncompressed =
        (uncompressed_table_region_data_t*) user_register_content[
            UNCOMP_ROUTER_TABLE];

    app_id = uncompressed->app_id;
    total_entries_in_uncompressed_router_table =
        uncompressed->uncompressed_table.size;
    log_info(
        "app id %d, uncompress total entries %d",
        app_id, total_entries_in_uncompressed_router_table);
}

//! \brief get compressor cores
bool initialise_compressor_cores(){
    // locate the data point for compressor cores
    uint32_t n_region_pairs = user_register_content[REGION_ADDRESSES][N_PAIRS];
    uint32_t hop = START_OF_ADDRESSES_DATA + (
        n_region_pairs * ADDRESS_PAIR_LENGTH);

    log_debug(" n region pairs = %d, hop = %d", n_region_pairs, hop);

    // get n compression cores and update trackers
    n_compression_cores =
        user_register_content[REGION_ADDRESSES][hop + N_COMPRESSOR_CORES];

    n_available_compression_cores = n_compression_cores;
    log_debug("%d comps cores available", n_available_compression_cores);

    // malloc dtcm for this
    compressor_cores = MALLOC(n_compression_cores * sizeof(uint32_t));
    // verify malloc worked
    if (compressor_cores == NULL){
        log_error("failed to allocate memory for the compressor cores");
        return false;
    }

    for (uint32_t core=0; core < n_compression_cores; core++){
        log_debug(
            "compressor core id at index %d is %d",
            core,
            user_register_content[REGION_ADDRESSES][
                hop + N_COMPRESSOR_CORES + START_OF_COMP_CORE_IDS + core]);
    }

    // populate with compressor cores
    log_debug("start populate compression cores");
    for (uint32_t core=0; core < n_compression_cores; core++){
        compressor_cores[core] = user_register_content[REGION_ADDRESSES][
            hop + N_COMPRESSOR_CORES + START_OF_COMP_CORE_IDS + core];
    }
    log_debug("finished populate compression cores");

    // allocate memory for the trackers
    comp_core_mid_point = MALLOC(n_compression_cores * sizeof(int));
    if (comp_core_mid_point == NULL){
        log_error(
            "failed to allocate memory for tracking what the "
            "compression cores are doing");
        return false;
    }

    // set the trackers all to -1 as starting point. to ensure completeness
    for (uint32_t core = 0; core < n_compression_cores; core++){
        comp_core_mid_point[core] = DOING_NOWT;
    }

    // set up addresses tracker
    comp_cores_bf_tables =
        MALLOC(n_compression_cores * sizeof(comp_core_store_t));
    if(comp_cores_bf_tables == NULL){
        log_error(
            "failed to allocate memory for the holding of bitfield "
            "addresses per compressor core");
        return false;
    }

    // ensure all bits set properly as init
    for(uint32_t c_core = 0; c_core < n_compression_cores; c_core++){
        comp_cores_bf_tables[c_core].n_elements = 0;
        comp_cores_bf_tables[c_core].n_bit_fields = 0;
        comp_cores_bf_tables[c_core].compressed_table = NULL;
        comp_cores_bf_tables[c_core].elements = NULL;
    }

    return true;
}

//! \brief the callback for setting off the router compressor
bool initialise() {
    log_info("Setting up stuff to allow bitfield comp control class to occur.");

    // Get pointer to 1st virtual processor info struct in SRAM
    initialise_user_register_tracker();

    // get the compressor data flags (app id, compress only when needed,
    //compress as much as possible, x_entries
    initialise_routing_control_flags();

    // get the compressor cores stored in a array
    log_debug("start init of compressor cores");
    bool success_compressor_cores = initialise_compressor_cores();
    if(!success_compressor_cores){
        log_error("failed to init the compressor cores.");
        return false;
    }

    // set up the best compressed table
    last_compressed_table = MALLOC(
        routing_table_sdram_size_of_table(TARGET_LENGTH));
    if (last_compressed_table == NULL){
        log_error("failed to allocate best space");
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

    bool success_init = initialise();
    if (!success_init){
        log_error("failed to init");
        vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
        sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_FAIL;
        spin1_exit(0);
    }

    spin1_callback_on(SDP_PACKET_RX, sdp_handler, SDP_PRIORITY);

    // kick-start the process
    spin1_schedule_callback(
        start_compression_process, 0, 0, COMPRESSION_START_PRIORITY);

    // go
    log_debug("waiting for sycn");
    spin1_start(SYNC_WAIT);
    //spin1_pause
    //spin1_resume
}
