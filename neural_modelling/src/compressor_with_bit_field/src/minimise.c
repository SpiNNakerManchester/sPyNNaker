#include <stdbool.h>
#include <stdlib.h>
#include "spin1_api.h"
#include "include/ordered_covering.h"
#include "include/remove_default_routes.h"
#include <debug.h>
/*****************************************************************************/
/* SpiNNaker routing table minimisation with bitfield integration.
 *
 * Minimise a routing table loaded into SDRAM and load the minimised table into
 * the router using the specified application ID.
 *
 * the exit code is stored in the user1 register
 *
 * The memory address with tag "1" is expected contain the following struct
 * (entry_t is defined in `routing_table.h` but is described below).
 */

//! \brief struct for a bitfield address point
typedef struct _bit_field_list_element{
    // the address of the bitfield data
    address_t bit_field_address;
    // next element
    _bit_field_list_element *next;
}_bit_field_list_element;

//! \brief struct for a redundant packet list element
typedef struct _redundant_packet_list_element{
    // the n redundant packets
    uint n_redundant_packets;
    // next element
    _redundant_packet_list_element *next;
}_redundant_packet_list_element;

//! \brief struct for list of coverage by bitfield components
typedef struct _bit_field_by_coverage_first_element{
    // element
    uint32_t n_redundant_packets;
    // length of the list
    uint32_t length;
    // last element
    _bit_field_list_element last_element;
    // next element
    _bit_field_list_element first_element;
} _bit_field_by_coverage_first_element;

//! \brief struct for list of bitfield components
typedef struct _coverage_by_processor_first_element{
    // element
    uint32_t processor_id;
    // length of the list
    uint32_t length;
    // last element
    _redundant_packet_list_element last_element;
    // next element
    _redundant_packet_list_element first_element;
} _bit_field_by_processor_first_element;

//! \brief struct for list of bitfield components
typedef struct _bit_field_by_processor_first_element{
    // element
    uint32_t processor_id;
    // length of the list
    uint32_t length;
    // last element
    _bit_field_list_element last_element;
    // next element
    _bit_field_list_element first_element;
} _bit_field_by_processor_first_element;

//! \brief struct for a redundant packet list element
typedef struct _bit_field_by_coverage{
    // first element
    _bit_field_by_coverage_first_element *element;
    // last element
    _bit_field_by_coverage_first_element *last;
    // length
    uint length;
}_bit_field_by_coverage;


//! enum for the different states to report through the user2 address.
typedef enum exit_states_for_user_one{
    EXITED_CLEANLY = 0, EXIT_FAIL = 1
} exit_states_for_user_two;

//! enum mapping for elements in uncompressed routing table region
typedef enum uncompressed_routing_table_region_elements{
    APPLICATION_APP_ID = 0, COMPRESS_ONLY_WHEN_NEEDED = 1,
    COMPRESS_AS_MUCH_AS_POSSIBLE = 2, N_ENTRIES = 3
}uncompressed_routing_table_region_elements;

//! enum mapping user register to data that's in there (only used by
//! programmer for documentation)
typedef enum user_register_maps{
    APPLICATION_POINTER_TABLE = 0, UNCOMPRESSED_ROUTER_TABLE = 1,
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

//! enum stating the compoennts of a bitfield struct
typedef enum bit_field_data_elements{
    BIT_FIELD_BASE_KEY = 0, BIT_FIELD_N_WORDS = 1, START_OF_BIT_FIELD_DATA = 2
} bit_field_data_elements;

//! callback priorities
typedef enum priorities{
    TIMER_TICK = 0, COMPRESSION_START = 3
}priorities;

//! expected size to work to in router entries
#define _MAX_SUPPORTED_LENGTH 1023

//! bits in a word
#define _BITS_IN_A_WORD 32

//! bit shift for the app id for the route
#define ROUTE_APP_ID_BIT_SHIFT 24

//! neuron level mask
#define _NEURON_LEVEL_MASK 0xFFFFFFFF

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
table_t last_compressed_table = NULL;

//! the list of bitfields in sorted order based off best effect.
_bit_field_data_t * sorted_bit_fields = NULL;

//! the bitfield by processor global holder
_bit_field_by_processor_first_element *bit_field_by_processor;


//! \brief reads in the addresses region and from there reads in the key atom
// map and from there searches for a given key. when found, returns the n atoms
//! \param[in] key: the key to locate n atoms for
//! \return atom for the key
void _minimise_locate_key_atom_map(uint32_t key){
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
            user_register_content[REGION_ADDRESSES][
                position_in_address_region + KEY_TO_ATOM_REGION];

        // read how many keys atom pairs there are
        uint32_t position_in_key_atom_pair = 0;
        uint32_t n_key_atom_pairs =
            key_atom_sdram_address[position_in_key_atom_pair];
        position_in_key_atom_pair += 1;

        // cycle through keys in this region looking for the key find atoms of
        for (uint32_t key_atom_pair_id = 0; key_atom_pair_id <
                n_key_atom_pairs; key_atom_pair_id++){
            uint32_t key_to_check = key_atom_sdram_address[
                position_in_key_atom_pair + SRC_BASE_KEY];

            // if key is correct, return atoms
            if (key_to_check == key){
                return key_atom_sdram_address[
                    position_in_key_atom_pair + SRC_N_ATOMS];
            }

            // move to next key pair
            position_in_key_atom_pair += LENGTH_OF_KEY_ATOM_PAIR;
        }

        // move to next key to atom sdram region
        position_in_address_region += ADDRESS_PAIR_LENGTH;
    }
    log_error("cannot find the key %d at all?! WTF", key);
    rt_error(RTE_SWERR);
}

//! \brief Load a routing table to the router.
//! \return bool saying if the table was loaded into the router or not
void minimise_load_routing_table_entries_to_router() {

    // Try to allocate sufficient room for the routing table.
    uint32_t entry_id = rtr_alloc_id(
        table->size,
        user_register_content[UNCOMPRESSED_ROUTER_TABLE][APPLICATION_APP_ID]);

    if (entry_id == 0) {
        log_info("Unable to allocate routing table of size %u\n", table->size);
        vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
        sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_FAIL;
        rt_error(RTE_SWERR);
    }

    // Load entries into the table (provided the allocation succeeded).
    // Note that although the allocation included the specified
    // application ID we also need to include it as the most significant
    // byte in the route (see `sark_hw.c`).
    for (uint32_t i = 0; i < table->size; i++) {
        // extract entry from table
        entry_t entry = last_compressed_table->entries[i];
        // merge app id to route
        uint32_t route = entry.route | (app_id << ROUTE_APP_ID_BIT_SHIFT);
        // set on the router
        rtr_mc_set(
            entry_id + i, entry.key_mask.key, entry.key_mask.mask, route);
    }
}

//! \brief reads a bitfield and deduces how many bits are not set
uint32_t minimise_detect_redundant_packet_count(
        address_t start_of_bit_field_struct){
    uint32_t n_filtered_packets = 0;
    uint32_t n_neurons = _minimise_locate_key_atom_map(
        start_of_bit_field_struct[BIT_FIELD_BASE_KEY]);
    for (uint neuron_id = 0; neuron_id < n_neurons; neuron_id++){
        if (!bit_field_test(
                start_of_bit_field_struct[START_OF_BIT_FIELD_DATA],
                neuron_id)){
            n_filtered_packets += 1;
        }
    }
    return n_filtered_packets;
}

//! \brief orders the bitfields for the binary search based off the impact
//! made in reducing the redundant packet processing on cores.
//! \param[in] _bit_field_by_coverage:
//! \param[in] coverage_by_processor_first_element
//! \return None
void minimise_order_bit_fields_based_on_impact(
        _bit_field_by_coverage bit_field_by_coverage,
        _coverage_by_processor_first_element, coverage_by_processor){

}

//! \brief reads in bitfields, makes a few maps, sorts into most priority.
//! \return bool that states if it succeeded or not.
bool minimise_read_in_bit_fields(){

    // count how many bitfields there are in total
    uint position_in_region_data = 0;
    uint32_t n_pairs_of_addresses =
        user_register_content[REGION_ADDRESSES][position_in_region_data];
    position_in_region_data += 1;

    // malloc the holders for the dicts that were going to build
    // holder for list of processor id to the
    bit_field_by_processor = MALLOC(
        n_pairs_of_addresses * sizeof(_bit_field_by_processor_first_element*));
    if (bit_field_by_processor == NULL){
        log_error("failed to alloc memory for bit_field_by_region_address");
        return false;
    }

    // holder for redundant packets by processor
    _coverage_by_processor_first_element processor_coverage = MALLOC(
        n_pairs_of_addresses * sizeof(_coverage_by_processor_first_element));
    if (processor_coverage == NULL){
        log_error("failed to alloc memory for processor_coverage");
        return false;
    }

    // track how many redundant packets there are
    _bit_field_by_coverage bit_field_by_coverage = MALLOC(
        sizeof(_bit_field_by_coverage));
    if(bit_field_by_coverage == NULL){
        log_error("failed to alloc memory for bit_field_by_coverage");
        return false;
    }
    bit_field_by_coverage->element = NULL;
    bit_field_by_coverage->last = NULL;


    // iterate through a processors bitfields region and populate dicts
    for (uint region_id = 0; region_id < n_pairs_of_addresses; region_id++){
        address_t bit_field_address = user_register_content[REGION_ADDRESSES][
            position_in_region_data + BITFIELD_REGION];
        uint processor = user_register_content[REGION_ADDRESSES][
            position_in_region_data + PROCESSOR_ID];
        position_in_region_data += ADDRESS_PAIR_LENGTH;

        // cycle through bitfields stored in bitfield region
        uint position_in_bit_field_region = 0;
        uint n_bit_fields = bit_field_address[position_in_bit_field_region];
        position_in_bit_field_region += 1;
        for(uint bit_field_id = 0; bit_field_id < n_bit_fields;
                bit_field_id++){

            // determine redundant packets count
            uint n_redundant_packets = minimise_detect_redundant_packet_count(
                bit_field_address[position_in_bit_field_region]);

            bit_field_by_coverage

            // update position in search
            n_words_read = bit_field_address[
                position_in_bit_field_region + BIT_FIELD_N_WORDS];
            position_in_bit_field_region +=
                START_OF_BIT_FIELD_DATA + n_words_read;
        }
    }

    // order the bitfields based off the impact to cores redundant packet
    // processing
    minimise_order_bit_fields_based_on_impact(
        bit_field_by_coverage, processor_coverage);
    return true;
}


//! \brief starts the work for the compression search
void minimise_start_compression_selection_process(){

    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
    log_info("read in bitfields");
    bool success_reading_in_bit_fields = minimise_read_in_bit_fields();
    log_info("finished reading in bitfields");
    if (! success_reading_in_bit_fields){
        sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_FAIL;
    }

    log_info("start binary search");
    minimise_start_binary_search();
    log_info("finish binary search");

    // if the search ended on a failure, regenerate the best one
    log_info("check the last search vs the best search");
    if (last_search_point != best_search_point){
        log_info("regenerating best combination");
        minimise_binary_search(best_search_point);
        log_info("finished regenerating best combination");
    }

    // load router entries into router
    log_info("load the routing table entries into the router");
    minimise_load_routing_table_entries_to_router();
    log_info("finished loading the routing table");


    // remove merged bitfields from the cores bitfields
    log_info("start the removal of the bitfields from the chips cores "
             "bitfield regions.");
    minimise_remove_merged_bitfields_from_cores();
    log_info("finished the removal of the bitfields from the chips cores "
             "bitfields regions.")
}

//! \brief sets up a tracker for the user registers so that its easier to use
//!  during coding.
void initialise_user_register_tracker(){
    log_info("set up user register tracker (easier reading)");
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
    user_register_content[APPLICATION_POINTER_TABLE] =
        (address_t) sark_virtual_processor_info[spin1_get_core_id()].user0;
    user_register_content[UNCOMPRESSED_ROUTER_TABLE] =
        (address_t) sark_virtual_processor_info[spin1_get_core_id()].user1;
    user_register_content[REGION_ADDRESSES] =
        (address_t) sark_virtual_processor_info[spin1_get_core_id()].user2;
    user_register_content[USABLE_SDRAM_REGIONS] =
        (address_t) sark_virtual_processor_info[spin1_get_core_id()].user3;
    log_info("finished setting up register tracker: \n\n""
             "user0 = %d\n user1 = %d\n user2 = %d\n user3 = %d",
             user_register_content[APPLICATION_POINTER_TABLE],
             user_register_content[UNCOMPRESSED_ROUTER_TABLE],
             user_register_content[REGION_ADDRESSES],
             user_register_content[USABLE_SDRAM_REGIONS]);
}

void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);
    finish_compression_flag +=1;

//! \brief sets up the timer so that a compression cycle can be measured
void initialise_timer_setup(){
    log_info("extracting time per compression iteration");

    // get region addresses (as time per compression is at the bottom of that
    // data)
    address_t addresses_region =
        user_register_content[REGION_ADDRESSES];

    // deduce bottom
    uint32_t x_region_pairs = addresses_region[0];
    uint32_t read_location = 1 + x_region_pairs * ADDRESS_PAIR_LENGTH;

    // extract time per compression
    time_per_iteration = addresses_region[read_location];

    // set timer tick period
    spin1_set_timer_tick(timer_period);
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);

    log_info(
        "finished extraction time per compression iteration: which was %d",
        time_per_iteration);
}

//! \brief the callback for setting off the router compressor
void initialise() {
    log_info("Setting up stuff to allow bitfield compression to occur.");

    // Get pointer to 1st virtual processor info struct in SRAM
    initialise_user_register_tracker();

    // build the fake heap for allocating memory
    log_info("setting up fake heap for sdram usage");
    platform_new_heap_creation(user_register_content[USABLE_SDRAM_REGIONS]);
    log_info("finished setting up fake heap for sdram usage");

    initialise_timer_setup();
}

//! \brief the main entrance.
void c_main(void) {
    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));

    initialise();

    // kick-start the process
    spin1_schedule_callback(
        minimise_start_compression_selection_process, 0, 0, COMPRESSION_START);

    // go
    spin1_start(SYNC_NOWAIT);
    spin1_pause
    spin1_resume
}
