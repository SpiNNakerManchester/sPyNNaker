#include <bit_field.h>
#include <utils.h>
#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>
#include <neuron/population_table/population_table.h>
#include <neuron/direct_synapses.h>
#include <neuron/synapse_row.h>

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

// used to store the dtcm based master pop entries. (used during pop table
// init, and reading back synaptic rows).
address_t direct_synapses_address;

// storage location for the list of vertex addresses
vertex_memory_regions_addresses** vertex_addresses;

// the number of vertex regions to process
uint32_t n_vertex_regions = 0;

//! a fake bitfield holder. used to circumvent the need for a bitfield in the
//! master pop table, which we are trying to generate with the use of the
//! master pop table. chicken vs egg.
bit_field_t* fake_bit_fields;

//! \brief used to hold sdram read row
uint32_t * row_data;

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
        sizeof(vertex_memory_regions_addresses*) * n_vertex_regions);

    // check dtcm was allocated
    if (vertex_addresses == NULL){
        log_error("cant allocate dtcm for the vertex region addresses");
        rt_error(RTE_ABORT);
    }

    // allocate each regions dtcm and read in data
    for (uint32_t vertex_region_index = 0;
            vertex_region_index < n_vertex_regions;
            vertex_region_index++){

        // allocate dtcm for region struct.
        vertex_addresses[vertex_region_index] =
            (vertex_memory_regions_addresses *) spin1_malloc(
                sizeof(vertex_memory_regions_addresses));

        // check dtcm was allocated
        if (vertex_addresses[vertex_region_index] == NULL){
            log_error("cant allocate dtcm for vertex %d regions",
                      vertex_region_index);
            rt_error(RTE_ABORT);
        }

        // read in a vertex memory regions
        spin1_memcpy(
            vertex_addresses[vertex_region_index], &data[position],
            sizeof(vertex_memory_regions_addresses));

        log_info(
            "vertex %d master_pop_table_base_address = %0x",
             vertex_region_index,
             vertex_addresses[vertex_region_index]->master_pop_base_address);
        log_info(
            "vertex %d synaptic_matrix_base_address = %0x",
             vertex_region_index,
             vertex_addresses[
                vertex_region_index]->synaptic_matrix_base_address);
        log_info(
            "vertex %d bit_field_base_address = %0x",
             vertex_region_index,
             vertex_addresses[vertex_region_index]->bit_field_base_address);
        log_info(
            "vertex %d synapse_params_region_base_address = %0x",
             vertex_region_index,
             vertex_addresses[
                vertex_region_index]->synapse_params_region_base_address);
        log_info(
            "vertex %d direct_matrix_region_base_address = %0x",
             vertex_region_index,
             vertex_addresses[
                vertex_region_index]->direct_matrix_region_base_address);

        // update sdram tracker
        position += (sizeof(vertex_memory_regions_addresses) /
                     BYTE_TO_WORD_CONVERSION);
    }
}

//! \brief deduces n neurons from the mask
//! \param[in] mask: the mask to convert to n_neurons
//! \return the number of neurons covered in this mask
uint32_t _n_neurons_from_mask(uint32_t mask){

    return next_power_of_2(~mask);
}

//! \brief deduces the n words for n neurons
//! \param[in] n_neurons: the n neurons to convert to n words
//! \return the number of words to cover the number of neurons
uint32_t _n_words_from_n_neurons(uint32_t n_neurons){
    return get_bit_field_size(n_neurons);
}

//! \brief creates a fake bitfield where every bit is set to 1.
//! \return bool, which states if the creation of the fake bitfield was
//!               successful or not.
bool _create_fake_bit_field(){
    fake_bit_fields = spin1_malloc(
        population_table_length() * sizeof(bit_field_t));
    if (fake_bit_fields == NULL){
        log_error("failed to alloc dtcm for the fake bitfield holders");
        return false;
    }

    // iterate through the master pop entries
    for (uint32_t master_pop_entry=0;
            master_pop_entry < population_table_length();
            master_pop_entry++){

        // determine n_neurons
        uint32_t mask = population_table_get_mask_for_entry(master_pop_entry);
        uint32_t n_neurons = _n_neurons_from_mask(mask);
        log_info("entry %d, mask = %0x, n_neurons = %d",
                 master_pop_entry, mask, n_neurons);

        // generate the bitfield for this master pop entry
        uint32_t n_words = _n_words_from_n_neurons(n_neurons);
        fake_bit_fields[master_pop_entry] =
            (bit_field_t) spin1_malloc(n_words * sizeof(bit_field_t));
        if (fake_bit_fields[master_pop_entry] == NULL){
            log_error("could not allocate dtcm for bit field");
            return false;
        }

        // set bitfield elements to 1 and store in fake bitfields.
        set_bit_field((bit_field_t)fake_bit_fields[master_pop_entry], n_words);
    }
    log_info("finished fake bit field");
    return true;
}

void _print_fake_bit_field(){
    uint32_t length = population_table_length();
    for (uint32_t bit_field_index = 0; bit_field_index < length;
            bit_field_index++){
        log_info("\n\nfield for index %d", bit_field_index);
        bit_field_t field = (bit_field_t) fake_bit_fields[bit_field_index];
        uint32_t mask = population_table_get_mask_for_entry(bit_field_index);
        uint32_t n_neurons = _n_neurons_from_mask(mask);
        for (uint32_t neuron_id = 0; neuron_id < n_neurons; neuron_id ++){
            if (bit_field_test(field, neuron_id)){
                log_info("neuron id %d was set", neuron_id);
            }
            else{
                log_info("neuron id %d was not set", neuron_id);
            }
        }
    }
    log_info("finished bit field print");
}

//! \brief sets up the master pop table and synaptic matrix for the bit field
//!        processing
//! \param[in] vertex_id: the index in the memory region paths.
//! \return: bool that states if the init was successful or not.
bool initialise(uint32_t vertex_id){

    // init the synapses to get direct synapse address
    if (!direct_synapses_initialise(
            vertex_addresses[vertex_id]->direct_matrix_region_base_address,
            &direct_synapses_address)) {
        log_error("failed to init the synapses. failing");
        return false;
    }

    // init the master pop table
    if (!population_table_initialise(
            vertex_addresses[vertex_id]->master_pop_base_address,
            vertex_addresses[vertex_id]->synaptic_matrix_base_address,
            direct_synapses_address, &row_max_n_words)) {
        log_error("failed to init the master pop table. failing");
        return false;
    }

    log_info(" elements in master pop table is %d \n and max rows is %d",
             population_table_length(), row_max_n_words);

    // set up a fake bitfield so that it always says there's something to read
    if (!_create_fake_bit_field()){
        log_error("failed to create fake bit field");
        return false;
    }

    // print fake bitfield
    _print_fake_bit_field();

    // set up a sdram read for a row
    log_info("allocating dtcm for row data");
    row_data = spin1_malloc(row_max_n_words * sizeof(uint32_t));
    if (row_data == NULL){
        log_error("could not allocate dtcm for the row data");
        return false;
    }
    log_info("finished dtcm for row data");
    // set up the fake connectivity lookup into the master pop table

    population_table_set_connectivity_lookup(fake_bit_fields);
    log_info("finished pop table set connectivity lookup");

    return true;
}

//! \brief checks plastic and fixed elements to see if there is a target.
//! \param[in] row: the synaptic row
//! \return bool stating true if there is target, false if no target.
bool process_synaptic_row(synaptic_row_t row){
    // get address of plastic region from row
    if(synapse_row_plastic_size(row) > 0){
        return true;
    }
    else{
        // Get address of non-plastic region from row
        address_t fixed_region_address = synapse_row_fixed_region(row);
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

//! \brief do sdram read to get synaptic row
//! \param[in] row_address: the sdram address to read
//! \param[in] n_bytes_to_transfer: how many bytes to read to get the
//!                                 synaptic row
//! \return bool which states true if there is target, false if no target.
bool _do_sdram_read_and_test(
        address_t row_address, uint32_t n_bytes_to_transfer){
    spin1_memcpy(row_data, row_address, n_bytes_to_transfer);
    return process_synaptic_row(row_data);
}

//! \brief creates the bitfield for this master pop table and synaptic matrix
//! \param[in] vertex_id: the index in the regions.
//! \return bool that states if it was successful at generating the bitfield
bool generate_bit_field(uint32_t vertex_id){

    // write how many entries (thus bitfields) are to be generated into sdram

    uint32_t position = 0;
    log_info("bit_field_base_address");
    address_t bit_field_base_address =
        vertex_addresses[vertex_id]->bit_field_base_address;
    log_info("mem cpy for pop length");
    bit_field_base_address[position] = population_table_length();
    log_info("update position");
    position ++;

    // iterate through the master pop entries
    log_info("starting master pop entry bit field generation");
    for (uint32_t master_pop_entry=0;
            master_pop_entry < population_table_length();
            master_pop_entry++){

        // determine keys masks and n_neurons
        spike_t key = population_table_get_spike_for_index(master_pop_entry);
        uint32_t mask = population_table_get_mask_for_entry(master_pop_entry);
        uint32_t n_neurons = _n_neurons_from_mask(mask);

        // generate the bitfield for this master pop entry
        uint32_t n_words = _n_words_from_n_neurons(n_neurons);

        log_info("pop entry %d, key = %0x, mask = %0x, n_neurons = %d",
                 master_pop_entry, key, mask, n_neurons);
        bit_field_t bit_field = spin1_malloc(n_words * sizeof(uint32_t));
        if (bit_field == NULL){
            log_error("could not allocate dtcm for bit field");
            return false;
        }

        // set the bitfield to 0. so assuming a miss on everything
        clear_bit_field(bit_field, n_words);
        log_info("cleared bit field");

        // update sdram with size of this bitfield
        bit_field_base_address[position] = n_words;
        position ++;

        // iterate through neurons and ask for rows from master pop table
        log_info("searching neuron ids");
        for (uint32_t neuron_id =0; neuron_id < n_neurons; neuron_id++){

            // update key with neuron id
            spike_t new_key = key & (spike_t) neuron_id;
            log_info("new key for neurons %d is %0x", neuron_id, new_key);

            // holder for the bytes to transfer if we need to read sdram.
            size_t n_bytes_to_transfer;
            if (population_table_get_first_address(
                    new_key, &row_address, &n_bytes_to_transfer)){

                log_info("after got address");
                // This is a direct row to process, so will have 1 target, so
                // no need to go further
                if (n_bytes_to_transfer == 0) {
                    log_info("direct synapse");
                    bit_field_set(bit_field, neuron_id);
                } else {
                    // sdram read (faking dma transfer)
                    log_info("dma read synapse");
                    if(_do_sdram_read_and_test(
                            row_address, n_bytes_to_transfer)){
                        bit_field_set(bit_field, neuron_id);
                    }
                }
            }
            else{
                log_info("should never get here!!!");
            }
            // if returned false, then the bitfield should be set to 0.
            // Which its by default already set to. so do nothing. so no else.
        }

        // write bitfield to sdram.
        log_info("writing bitfield to sdram for core use");
        spin1_memcpy(&bit_field_base_address[position], bit_field,
                     n_words * BYTE_TO_WORD_CONVERSION);
        position += n_words;

        // free dtcm of bitfield.
        log_info("freeing the bitfield dtcm");
        sark_free(bit_field);
    }
    return true;
}

//! \brief frees the dtcm allocated so that the next cycle doesnt run out of
//!        dtcm
//! \return bool that states if it was successful at freeing the dtcm
bool free_dtcm(){

    // free the fake bit field.
    log_info("freeing fake b it field");
    for (uint32_t bit_field_index = 0;
            bit_field_index < population_table_length();
            bit_field_index++){
        log_info("freeing bitfield in index %d", bit_field_index);
        sark_free(fake_bit_fields[bit_field_index]);
    }
    log_info("freeing top free bit field");
    sark_free(fake_bit_fields);

    // free pop table dtcm
    log_info("freeing pop table");
    if(!population_table_shut_down()){
        log_error("failed to shut down the master pop table");
        return false;
    }

    // free the allocated from synapses
    log_info("freeing direct synapses");
    sark_free(direct_synapses_address);

    // free the row data holder
    log_info("freeing row data");
    sark_free(row_data);
    log_info("done all freeing yey!");
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
        if(!initialise(vertex_id)){
            log_error(
                "failed to init the master pop and synaptic matrix for vertex"
                 " %d", vertex_id);
            rt_error(RTE_ABORT);
        }
        log_info("generating bit field for vertex %d", vertex_id);
        if(!generate_bit_field(vertex_id)){
            log_error(
                "failed to generate bitfield for the vertex %d", vertex_id);
            rt_error(RTE_ABORT);
        };
        log_info("freeing dtcm for vertex %d", vertex_id);
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
