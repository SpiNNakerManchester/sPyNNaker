#include "population_table/population_table.h"
#include "synapses.h"
#include "synapse_row.h"

#include <bit_field.h>
#include <utils.h>
#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>

//! location to hold memory addresses
typedef struct vertex_memory_regions_addresses {
    address_t master_pop_base_address;
    address_t synaptic_matrix_base_address;
    address_t bit_field_base_address;
    address_t synapse_params_region_base_address;
    address_t direct_matrix_region_base_address;
} vertex_memory_regions_addresses;

// byte to word conversion
#define BYTE_TO_WORD_CONVERSION 4

// does minimum neurons to sort out dtcm and get though the synapse init.
#define N_NEURONS 1

// does minimum synapse types to sort out dtcm and get though the synapse init.
#define N_SYNAPSE_TYPES 1

// used to store the row from the master pop / synaptic matrix, not going to
// be used in reality.
address_t row_address;

// used to store the max row size for dma reads (used when extracting a
// synapse row from sdram.
uint32_t row_max_n_words;

// storage location for the list of vertex addresses
vertex_memory_regions_addresses* vertex_addresses;

// the number of vertex regions to process
uint32_t n_vertex_regions = 0;

//! a fake bitfield holder. used to circumvent the need for a bitfield in the
//! master pop table, which we are trying to generate with the use of the
//! master pop table. chicken vs egg.
uint32_t* fake_bit_fields;

//! \brief some data holder for a single fixed synapse
static uint32_t single_fixed_synapse[4];

//! \brief used to hold sdram read row
uint32_t * row_data

//! \brief reads in the vertex region addresses
void read_in_addresses(){

    // get the data (linked to sdram tag 2 and assume the app ids match)
    address_t data = sark_tag_ptr(2, 0);

    // get how many vertex's we're to process
    int position = 0;
    n_vertex_regions = data[position];
    position += 1;

    // allocate dtcm for the vertex's
    vertex_addresses = spin1_malloc(
        sizeof(*vertex_memory_regions_addresses) * n_vertex_regions);

    // check dtcm was allocated
    if (vertex_addresses is NULL){
        log_error("cant allocate dtcm for the vertex region addresses");
        rt_error(RTE_ABORT);
    }

    // allocate each regions dtcm and read in data
    for (uint32_t vertex_region_index = 0;
            vertex_region_index < n_vertex_regions;
            vertex_region_index++){

        // allocate dtcm for region struct.
        vertex_addresses[vertex_region_index] = spin1_malloc(
            sizeof(vertex_memory_regions_addresses));

        // check dtcm was allocated
        if (vertex_addresses[vertex_region_index] == NULL){
            log_error("cant allocate dtcm for vertex %d regions",
                      vertex_region_index);
            rt_error(RTE_ABORT);
        }

        // read in a vertex memory regions
        spin1_memcpy(
            vertex_addresses[vertex_region_index], data[position],
            sizeof(vertex_memory_regions_addresses));

        // update sdram tracker
        position += (sizeof(vertex_memory_regions_addresses) /
                     BYTE_TO_WORD_CONVERSION);
    }
}

//! \brief creates a fake bitfield where every bit is set to 1.
//! \return bool, which states if the creation of the fake bitfield was
//!               successful or not.
bool _create_fake_bit_field(){
    fake_bit_fields = spin1_malloc(
        population_table_length() * sizeof(*bit_field_t));
    if (fake_bit_fields == NULL){
        log_error("failed to alloc dtcm for the fake bitfield holders");
        return false;
    }

    // iterate through the master pop entries
    for (uint32_t master_pop_entry=0;
            master_pop_entry < population_table_length();
            master_pop_entry++){

        // determine keys masks and n_neurons
        spike_t key = population_table_get_spike_for_index(master_pop_entry);
        uint32_t mask = population_table_get_mask_for_entry(master_pop_entry);
        uint32_t n_neurons = _n_neurons_from_mask(mask);

        // generate the bitfield for this master pop entry
        uint32_t n_words = _n_words_from_n_neurons(n_neurons);
        bit_field_t bit_field = spin1_malloc(n_words * sizeof(uint32_t));
        if (bit_field == NULL){
            log_error("could not allocate dtcm for bit field");
            return false;
        }

        // set bitfield elements to 1 and store in fake bitfields.
        set_bit_field(bit_field, n_words);
        fake_bit_fields[master_pop_entry] = bit_field;
    }
}

//! \brief sets up the master pop table and synaptic matrix for the bit field
//!        processing
//! \param[in] vertex_id: the index in the memory region paths.
//! \return: bool that states if the init was successful or not.
bool initialise_master_pop_table(uint32_t vertex_id){
    uint32_t *ring_buffer_to_input_buffer_left_shifts;
    address_t direct_synapses_address;

    // init the synapses to get direct synapse address
    if (!synapses_initialise(
            vertex_addresses[vertex_id].synapse_params_region_base_address,
            vertex_addresses[vertex_id].direct_matrix_region_base_address,
            N_NEURONS, N_SYNAPSE_TYPES,
            &ring_buffer_to_input_buffer_left_shifts,
            &direct_synapses_address)) {
        log_error("failed to init the synapses. failing");
        return false;
    }

    // Set up for single fixed synapses (data that is consistent per direct row)
    single_fixed_synapse[0] = 0;
    single_fixed_synapse[1] = 1;
    single_fixed_synapse[2] = 0;

    // init the master pop table
    if (!population_table_initialise(
            vertex_addresses[vertex_id].master_pop_base_address,
            vertex_addresses[vertex_id].synaptic_matrix_base_address,
            direct_synapses_address, &row_max_n_words)) {
        log_error("failed to init the master pop table. failing");
        return false;
    }

    // set up a fake bitfield so that it always says there's something to read
    if (!_create_fake_bit_field()){
        log_error("failed to create fake bit field");
        return false;
    }

    // set up a sdram read for a row
    row_data = spin1_malloc(row_max_n_words * sizeof(uint32_t))
    if (row_data == NULL){
        log_error("could not allocate dtcm for the row data");
        return false;
    }

    // set up the fake connectivity lookup into the master pop table
    population_table_set_connectivity_lookup(fake_bit_fields);

    return true;
}

//! \brief checks plastic and fixed elements to see if there is a target.
//! \param[in] row: the synaptic row
//! \return bool stating true if there is target, false if no target.
bool process_synaptic_row(synaptic_row_t row){
    // get address of plastic region from row
    if(synapse_row_plastic_size(row_address) > 0){
        return true;
    }
    else{
        // Get address of non-plastic region from row
        address_t fixed_region_address =
            synapse_row_fixed_region(single_fixed_synapse);
        uint32_t fixed_synapse =
            synapse_row_num_fixed_synapses(fixed_region_address);
        if (fixed_synapse==0){
            return false;
        }
        else{
            return true;
        }
    }
}

//! \brief processes direct row based synaptic matrix
//! \param[in] row_address: the address of the row.
bool _do_direct_row(address_t row_address) {
    single_fixed_synapse[3] = (uint32_t) row_address[0];
    return process_synaptic_row(single_fixed_synapse);
}

//! \brief do sdram read to get synaptic row
//! \param[in] row_address: the sdram address to read
//! \param[in] n_bytes_to_transfer: how many bytes to read to get the
//!                                 synaptic row
//! \return bool which states true if there is target, false if no target.
bool _do_sdram_read(row_address, n_bytes_to_transfer){
    spin1_memcpy(row_data, row_address, n_bytes_to_transfer);
    return process_synaptic_row(row_data);
}

//! \brief deduces n neurons from the mask
//! \param[in] mask: the mask to convert to n_neurons
//! \return the number of neurons covered in this mask
uint32_t _n_neurons_from_mask(uint32_t mask){
    return next_power_of_2(mask);
}

//! \brief deduces the n words for n neurons
//! \param[in] n_neurons: the n neurons to convert to n words
//! \return the number of words to cover the number of neurons
uint32_t _n_words_from_n_neurons(n_neurons){
    return get_bit_field_size(n_neurons);
}

//! \brief creates the bitfield for this master pop table and synaptic matrix
//! \param[in] vertex_id: the index in the regions.
//! \return bool that states if it was successful at generating the bitfield
bool generate_bit_field(uint32_t vertex_id){

    // write how many entries (thus bitfields) are to be generated into sdram
    uint32_t position = 0;
    address_t bit_field_base_address = vertex_addresses[vertex_id];
    bit_field_base_address[position] = population_table_length();
    position ++;

    // iterate through the master pop entries
    for (uint32_t master_pop_entry=0;
            master_pop_entry < population_table_length();
            master_pop_entry++){

        // determine keys masks and n_neurons
        spike_t key = population_table_get_spike_for_index(master_pop_entry);
        uint32_t mask = population_table_get_mask_for_entry(master_pop_entry);
        uint32_t n_neurons = _n_neurons_from_mask(mask);

        // generate the bitfield for this master pop entry
        uint32_t n_words = _n_words_from_n_neurons(n_neurons);
        bit_field_t bit_field = spin1_malloc(n_words * sizeof(uint32_t));
        if (bit_field == NULL){
            log_error("could not allocate dtcm for bit field");
            return false;
        }

        // set the bitfield to 0. so assuming a miss on everything
        clear_bit_field(bit_field, n_words);

        // update sdram with size of this bitfield
        bit_field_base_address[position] = n_words;
        position ++;

        // iterate through neurons and ask for rows from master pop table
        for (uint32_t neuron_id =0; neuron_id < n_neurons; neuron_id++){

            // update key with neuron id
            spike_t new_key = key & (spike_t) neuron_id;

            // holder for the bytes to transfer if we need to read sdram.
            size_t n_bytes_to_transfer;
            if (population_table_get_first_address(
                    new_key, row_address, n_bytes_to_transfer)){

                // This is a direct row to process
                if (n_bytes_to_transfer == 0) {
                    if(_do_direct_row(row_address)){
                        bit_field_set(bit_field, neuron_id);
                    }
                // sdram read (faking dma transfer)
                } else {
                    _do_sdram_read(row_address, n_bytes_to_transfer);
                    setup_done = true;
                }
            }
            // if returned false, then the bitfield should be set to 0.
            // Which its by default already set to. so do nothing. so no else.
        }

        // write bitfield to sdram.
        spin1_memcpy(bit_field_base_address[position], bit_field,
                     n_words * BYTE_TO_WORD_CONVERSION);
        position += n_words;

        // free dtcm of bitfield.
        sark_free(bit_field);
    }
}

//! \brief frees the dtcm allocated so that the next cycle doesnt run out of
//!        dtcm
//! \return bool that states if it was successful at freeing the dtcm
bool free_dtcm(){

    // free pop table dtcm
    if(!population_table_shut_down()){
        log_error("failed to shut down the master pop table")
        return false;
    }

    // free synapses dtcm
    if(!synapses_shut_down()){
        log_error("failed to shut down the synapses")
        return false;
    }

    // free the fake bit field.
    sark_free(fake_bit_fields);

    // free the row data holder
    sark_free(row_data);
    return true;
}

void c_main(void) {
    // set to running state
    sark_cpu_state(CPU_STATE_RUN);

    log_info("starting the bit field expander");

    // read in sdram data
    read_in_addresses();

    // generate bit field for each vertex regions
    for (uint32_t vertex_id = 0; vertex_id < n_vertex_regions; vertex_id++){
        if(!initialise_master_pop_table(vertex_id)){
            log_error(
                "failed to init the master pop and synaptic matrix for vertex"
                 " %d", vertex_id);
            rt_error(RTE_ABORT);
        }
        if(!generate_bit_field(vertex_id)){
            log_error(
                "failed to generate bitfield for the vertex %d", vertex_id);
            rt_error(RTE_ABORT);
        };
        if(!free_dtcm()){
            log_error(
                "failed to free dtcm from the master pop and synapses for "
                "vertex %d", vertex_id);
            rt_error(RTE_ABORT);
        }
        log_info(
            "successfully processed the bitfield for vertex %d", vertex_id);
    }

    // done!
    log_info("Finished bitfield expander!");
}
