#include <spin1_api.h>
#include <debug.h>
#include <bit_field.h>
#include <sdp_no_scp.h>
#include "common-typedefs.h"
#include "../common/compressor_common/platform.h"
#include "../common/compressor_common/routing_table.h"
#include "../common/compressor_common/compression_sdp_formats.h"
/*****************************************************************************/
/* SpiNNaker routing table minimisation with bitfield integration control core.
 *
 * controls the attempt to minimise the router entries with bitfield
 * components.
 */

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
}_coverage;

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
    N_COMPRESSOR_CORES = 0, START_OF_COMPRESSOR_CORE_IDS = 1
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

//! flag for saying compression core doing nowt
#define DOING_NOWT -1

//! expected size to work to in router entries
#define _MAX_SUPPORTED_LENGTH 1023

//! \brief timeout on attempts to send sdp message
#define _SDP_TIMEOUT 100

//! bits in a word
#define _BITS_IN_A_WORD 32

//! bit shift for the app id for the route
#define ROUTE_APP_ID_BIT_SHIFT 24

//! word to byte multiplier
#define WORD_TO_BYTE_MULTIPLIER 4

//! size of x routing entries in bytes
#define X_ROUTING_TABLE_ENTRIES_SDRAM_SIZE 4

//! neuron level mask
#define _NEURON_LEVEL_MASK 0xFFFFFFFF

//! how many tables the uncompressed router table entries is
#define _N_UNCOMPRESSED_TABLE = 1

//! random port as 0 is in use by scamp/sark
#define RANDOM_PORT 4

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

//! how many entries are in the uncompressed version
uint32_t total_entries_in_uncompressed_router_table = 0;

//! the list of bitfields in sorted order based off best effect.
address_t * sorted_bit_fields;

//! the list of the addresses of the routing table entries for the bitfields 
//! and reduced routing table
address_t * bit_field_routing_tables;

//! list of bitfield associated processor ids. sorted order based off best
//! effort linked to sorted_bit_fields, but separate to avoid sdram rewrites
uint32_t * sorted_bit_fields_processor_ids;

//! list of processor ids which will be running the compressor binary
uint32_t * compressor_cores;

//! how many compression cores there are
uint32_t n_compression_cores;

//! how many compression cores are available
uint32_t n_available_compression_cores;

//! tracker for what each compressor core is doing (in terms of midpoints)
int * compression_testing_point;

//! the bitfield by processor global holder
_bit_field_by_processor_t* bit_field_by_processor;

//! the current length of the filled sorted bit field.
uint32_t sorted_bit_field_current_fill_loc = 0;

//! \brief sdp message to send control messages to compressors cores
sdp_msg_pure_data my_msg;

//! \brief try running compression on just the uncompressed (attempt to check
//!     that without bitfields compression will work).
//! \return bool saying success or failure of the compression
bool start_binary_search(){
    return false;
}

//! \brief compress the bitfields from the best location
void binary_search(){

}

//! \brief removes the merged bitfields from the application cores bitfield
//!        regions
void remove_merged_bitfields_from_cores(){

}

//! \brief the sdp control entrance.
void _sdp_handler(uint mailbox, uint port) {
    use(port);
    // get data from the sdp message
    sdp_msg_pure_data *msg = (sdp_msg_pure_data *) mailbox;
    log_info("received response");
    sark_msg_free((sdp_msg_t*) msg);
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

//! \brief reads in bitfields, makes a few maps, sorts into most priority.
//! \return bool that states if it succeeded or not.
bool read_in_bit_fields(){

    // count how many bitfields there are in total
    uint position_in_region_data = 0;
    uint n_bit_field_addresses = 0;
    uint32_t n_pairs_of_addresses =
        user_register_content[REGION_ADDRESSES][N_PAIRS];
    position_in_region_data = START_OF_ADDRESSES_DATA;
    log_info("n pairs of addresses = %d", n_pairs_of_addresses);

    // malloc the bt fields by processor
    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
    bit_field_by_processor = MALLOC(
        n_pairs_of_addresses * sizeof(_bit_field_by_processor_t));
    if (bit_field_by_processor == NULL){
        log_error("failed to allocate memory for pairs, if it fails here. "
                  "might as well give up");
        return false;
    }
    
    // build processor coverage by bitfield
    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
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
        log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
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
        log_info("bit_field_by_processor in region %d processor id = %d",
                 region_id, bit_field_by_processor[region_id].processor_id);

        // locate data for malloc memory calcs
        address_t bit_field_address = (address_t) user_register_content[
            REGION_ADDRESSES][position_in_region_data + BITFIELD_REGION];
        position_in_region_data += ADDRESS_PAIR_LENGTH;
        uint32_t pos_in_bitfield_region = N_BIT_FIELDS;
        uint32_t core_n_bit_fields = bit_field_address[pos_in_bitfield_region];
        pos_in_bitfield_region = START_OF_BIT_FIELD_TOP_DATA;
        n_bit_field_addresses += core_n_bit_fields;
        
        // track lengths
        proc_cov_by_bitfield[region_id]->length_of_list = core_n_bit_fields;
        bit_field_by_processor[region_id].length_of_list = core_n_bit_fields;
        log_info("bit field by processor with region %d, has length of %d",
                 region_id, core_n_bit_fields);
        
        // malloc for bitfield region addresses
        log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
        bit_field_by_processor[region_id].bit_field_addresses = MALLOC(
            core_n_bit_fields * sizeof(address_t));
        if (bit_field_by_processor[region_id].bit_field_addresses == NULL){
            log_error("failed to allocate memory for bitfield addresses for "
                      "region %d, might as well fail", region_id);
            return false; 
        }
        
        // malloc for n redundant packets
        log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
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
            log_info("prov cov by bitfield for region %d, redundant packets "
                     "at index %d, has n redundant packets of %d",
                     region_id, bit_field_id, n_redundant_packets);
            
            pos_in_bitfield_region += 
                START_OF_BIT_FIELD_DATA + bit_field_address[
                    pos_in_bitfield_region + BIT_FIELD_N_WORDS];
        }
    }

    // populate the bitfield by coverage
    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
    sorted_bit_fields = MALLOC(n_bit_field_addresses * sizeof(address_t));
    if(sorted_bit_fields == NULL){
        log_error("cannot allocate memory for the sorted bitfield addresses");
        return false;
    }

    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
    sorted_bit_fields_processor_ids =
        MALLOC(n_bit_field_addresses * sizeof(uint32_t));
    if (sorted_bit_fields_processor_ids == NULL){
        log_error("cannot allocate memory for the sorted bitfields with "
                  "processors ids");
        return false;
    }

    uint length_n_redundant_packets = 0;
    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
    uint * redundant_packets = MALLOC(n_bit_field_addresses * sizeof(uint));

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
    log_info("length of n redundant packets = %d", length_n_redundant_packets);

    // malloc space for the bitfield by coverage map
    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
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
        log_info("try to allocate memory of size %d for coverage at index %d",
                 sizeof(_coverage), r_packet_index);
        log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
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
        log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
        coverage[r_packet_index]->bit_field_addresses = MALLOC(
            n_bit_fields_with_same_x_r_packets * sizeof(address_t));
        if(coverage[r_packet_index]->bit_field_addresses == NULL){
            log_error("failed to allocate memory for the coverage on index %d"
                      " for addresses. might as well fail.", r_packet_index);
            return false;
        }
        
        // malloc list size for the corresponding processors ids for the 
        // bitfields
        log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
        log_info(
            "trying to allocate %d bytes, for x bitfields same xr packets %d",
            n_bit_fields_with_same_x_r_packets * sizeof(uint32_t),
            n_bit_fields_with_same_x_r_packets);
        coverage[r_packet_index]->processor_ids = MALLOC(
            n_bit_fields_with_same_x_r_packets * sizeof(uint32_t));
        if(coverage[r_packet_index]->processor_ids == NULL){
            log_error("failed to allocate memory for the coverage on index %d"
                      " for processors. might as well fail.", r_packet_index);
            return false;
        }
            
        // populate list of bitfields addresses which have same redundant 
        //packet count.
        log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
        log_info(
            "populating list of bitfield addresses with same packet count");
        for (uint region_id = 0; region_id < n_pairs_of_addresses; region_id++){
            log_info("prov cov for region id %d has length %d", region_id,
                     proc_cov_by_bitfield[region_id]->length_of_list);
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
        log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
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

//! \brief selects a compression core that's not doing anything yet
uint32_t select_compressor_core(uint32_t midpoint){
    for(uint32_t comp_core_index = 0; comp_core_index < n_compression_cores;
            comp_core_index++){
        if (compression_testing_point[comp_core_index] == DOING_NOWT){
            compression_testing_point[comp_core_index] = midpoint;
            n_available_compression_cores -= 1;
            return compressor_cores[comp_core_index];
        }
    }
    log_error("cant find a core to allocate to you");
    rt_error(RTE_SWERR);
    return 0;  // needed for compiler warning to shut up
}


//! \brief sends a SDP message to a compressor core to do compression with
//!  a number of bitfields
//! \param[in] n_bit_field_addresses: how many addresses the bitfields merged
//!  into
//! \param[in] mid_point: the mid point in the binary search
bool set_off_bit_field_compression(
        uint32_t n_bit_field_addresses, uint32_t mid_point){

    // allocate space for the compressed routing entries
    address_t compressed_address = MALLOC_SDRAM(
        routing_table_sdram_size_of_table(_MAX_SUPPORTED_LENGTH));
    if (compressed_address == NULL){
        log_error("failed to allocate sdram for compressed routing entries");
        return false;
    }
    log_info("address for compressed data is %d", compressed_address);

    // select compressor core to execute this
    uint32_t compressor_core_id = select_compressor_core(mid_point);

    // update sdp to right destination
    log_info("chip id = %d", spin1_get_chip_id());
    my_msg.srce_addr = spin1_get_chip_id();
    my_msg.dest_addr = spin1_get_chip_id();
    my_msg.flags = 0x07;
    log_info("core id =  %d", spin1_get_id());
    my_msg.srce_port = (RANDOM_PORT << PORT_SHIFT) | spin1_get_core_id();
    log_info("compressor core = %d", compressor_core_id);
    my_msg.dest_port = (RANDOM_PORT << PORT_SHIFT) | compressor_core_id;

    // deduce how many packets
    uint32_t total_packets = 1;
    uint32_t n_addresses_for_start =
        ITEMS_PER_DATA_PACKET - sizeof(start_stream_sdp_packet_t);
    if (n_addresses_for_start < n_bit_field_addresses){
        n_bit_field_addresses -= n_addresses_for_start;
        total_packets += n_bit_field_addresses / (
            ITEMS_PER_DATA_PACKET - sizeof(extra_stream_sdp_packet_t));
        uint32_t left_over = n_bit_field_addresses % (
            ITEMS_PER_DATA_PACKET - sizeof(extra_stream_sdp_packet_t));
        if (left_over != 0){
            total_packets += 1;
        }
    }
    log_info("n packets = %d", total_packets);

    // generate the packets and fire them to the compressor core
    uint32_t addresses_sent = 0;
    uint32_t addresses_this_message = 0;
    for (uint32_t packet_id =0; packet_id < total_packets; packet_id++){
        // if just one packet worth, set to left over addresses
        if ((n_bit_field_addresses - addresses_sent) <=
                ITEMS_PER_DATA_PACKET - sizeof(start_stream_sdp_packet_t)){
            addresses_this_message =
                n_bit_field_addresses - addresses_sent;
        } else{  // if more than 1 packet worth, max packet out
            if (packet_id == 0){  // first packet
                addresses_this_message =
                    ITEMS_PER_DATA_PACKET - sizeof(start_stream_sdp_packet_t);
            }
            else{  // extra packet
                 addresses_this_message =
                    ITEMS_PER_DATA_PACKET - sizeof(extra_stream_sdp_packet_t);
            }
        }

        log_info("addresses this message = %d", addresses_this_message);

        // set data components
        if (packet_id == 0){  // first packet
            log_info("addresses this message = %d", addresses_this_message);
            my_msg.data[COMMAND_CODE] = START_OF_COMPRESSION_DATA_STREAM;

            // create cast
            start_stream_sdp_packet_t* data = (start_stream_sdp_packet_t*)
                my_msg.data[START_OF_SPECIFIC_MESSAGE_DATA];

            // fill in
            data->n_sdp_packets_till_delivered = total_packets;
            data->address_for_compressed = compressed_address;
            data->fake_heap_data = user_register_content[USABLE_SDRAM_REGIONS];
            data->total_n_tables = n_bit_field_addresses;
            log_info("addresses this message = %d", addresses_this_message);
            data->n_tables_in_packet = addresses_this_message;
            log_info("addresses this message = %d", addresses_this_message);
            log_info("addresses this message = %d",  data->n_tables_in_packet);
            log_info(
                "mem cpy tables to dest = %d, from source = %d, bytes = %d",
                &data->tables, &bit_field_routing_tables[addresses_sent],
                addresses_this_message * WORD_TO_BYTE_MULTIPLIER);
            sark_mem_cpy(
                &data->tables, &bit_field_routing_tables[addresses_sent],
                addresses_this_message * WORD_TO_BYTE_MULTIPLIER);
            my_msg.length = (
                LENGTH_OF_SDP_HEADER + (
                    (addresses_this_message +
                     sizeof(start_stream_sdp_packet_t)) *
                    WORD_TO_BYTE_MULTIPLIER));
            log_info(
                "messgae contains command code %d, n sdp packets till "
                "delivered %d, address for compressed %d, fake heap data "
                "address %d total n tables %d, n tables in packet %d",
                my_msg.data[COMMAND_CODE], data->n_sdp_packets_till_delivered,
                data->address_for_compressed, data->fake_heap_data,
                data->total_n_tables);
            log_info("message length = %d", my_msg.length);
        }
        else{  // extra packets
            log_info("sending extra packet id = %d", packet_id);
            my_msg.data[COMMAND_CODE] = EXTRA_DATA_FOR_COMPRESSION_DATA_STREAM;
            extra_stream_sdp_packet_t* data =(extra_stream_sdp_packet_t*)
                my_msg.data[START_OF_SPECIFIC_MESSAGE_DATA];
            data->n_tables_in_packet = addresses_this_message;
            sark_mem_cpy(
                &data->tables, &bit_field_routing_tables[addresses_sent],
                addresses_this_message * WORD_TO_BYTE_MULTIPLIER);
            my_msg.length = (
                LENGTH_OF_SDP_HEADER + (
                    (addresses_this_message +
                     sizeof(extra_stream_sdp_packet_t)) *
                    WORD_TO_BYTE_MULTIPLIER));
            log_info("message length = %d", my_msg.length);
        }

        // update location in addresses
        addresses_sent += addresses_this_message;

        // send sdp packet
        while (!spin1_send_sdp_msg((sdp_msg_t *) &my_msg, _SDP_TIMEOUT)) {
            // Empty body
        }
        log_info("sent message");
    }
    return true;
}

//! \brief sets off the basic compression without any bitfields
bool set_off_no_bit_field_compression(){
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
        &user_register_content[UNCOMP_ROUTER_TABLE][N_ENTRIES], sdram_used);
    
    // set up the bitfield routing tables so that it'll map down below
    bit_field_routing_tables = MALLOC(sizeof(address_t*));
    bit_field_routing_tables[0] = sdram_clone_of_routing_table;

    // run the allocation and set off of a compressor core
    bool success = set_off_bit_field_compression(1, 0);

    // free memory
    FREE(bit_field_routing_tables);

    // return success
    return success;

}

//! \brief starts the work for the compression search
bool start_process(){
    // will use this many palces. so exrtact at top
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;

    // set off
    log_info("set off 1 compressor core to explore no bitfield compression");
    bool success_basic_compression = set_off_no_bit_field_compression(0, 0);

    // check we set off the none bitfield one successfully
    if (! success_basic_compression){
        log_error("failed to set off basic compression");
        sark_virtual_processor_info[spin1_get_core_id()].user1 = EXIT_MALLOC;
        return false;
    }

    log_info("read in bitfields");
    bool success_reading_in_bit_fields = read_in_bit_fields();
    log_info("finished reading in bitfields");
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

    // if the search ended on a failure, regenerate the best one
    log_info("check the last search vs the best search");
    if (last_search_point != best_search_point){
        log_info("regenerating best combination");
        binary_search();
        log_info("finished regenerating best combination");
    }

    // load router entries into router
    log_info("load the routing table entries into the router");
    load_routing_table_entries_to_router();
    log_info("finished loading the routing table");


    // remove merged bitfields from the cores bitfields
    log_info("start the removal of the bitfields from the chips cores "
             "bitfield regions.");
    remove_merged_bitfields_from_cores();
    log_info("finished the removal of the bitfields from the chips cores "
             "bitfields regions.");
    return true;
}

void start_compression_selection_process(){
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
            hop + N_COMPRESSOR_CORES + START_OF_COMPRESSOR_CORE_IDS + core];
    }

    // allocate memory for the trackers
    compression_testing_point = MALLOC(n_compression_cores * sizeof(int));
    if (compression_testing_point == NULL){
        log_error("failed to allocate memory for tracking what the "
                  "compression cores are doing");
        return false;
    }

    // set the trackers all to -1 as starting point. to ensure completeness
    for (uint32_t core = 0; core < n_compression_cores; core++){
        compression_testing_point[core] = DOING_NOWT;
    }
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
        start_compression_selection_process, 0, 0,
        COMPRESSION_START_PRIORITY);
    spin1_callback_on(SDP_PACKET_RX, _sdp_handler, SDP_PRIORITY);

    // go
    spin1_start(SYNC_WAIT);
    //spin1_pause
    //spin1_resume
}
