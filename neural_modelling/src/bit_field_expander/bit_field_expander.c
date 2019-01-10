#include <bit_field.h>
#include <utils.h>
#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>
#include <neuron/regions.h>
#include <neuron/population_table/population_table.h>
#include <neuron/direct_synapses.h>
#include <neuron/synapse_row.h>

//! store of key to n atoms map
typedef struct key_to_max_atoms_map {
    uint32_t key;
    uint32_t n_atoms;
} key_to_max_atoms_map;

// byte to word conversion
#define BYTE_TO_WORD_CONVERSION 4

// does minimum neurons to sort out dtcm and get though the synapse init.
#define N_NEURONS 1

// does minimum synapse types to sort out dtcm and get though the synapse init.
#define N_SYNAPSE_TYPES 1

// used to store the row from the master pop / synaptic matrix, not going to
// be used in reality.
address_t row_address;

//! master pop address
address_t master_pop_base_address;

// synaptic matrix base address
address_t synaptic_matrix_base_address;

// bitfield base address
address_t bit_field_base_address;

// direct matrix base address
address_t direct_matrix_region_base_address;

// bitfield builder data base address
address_t bit_field_builder_base_address;

// used to store the dtcm based master pop entries. (used during pop table
// init, and reading back synaptic rows).
address_t direct_synapses_address;

// used to store the max row size for dma reads (used when extracting a
// synapse row from sdram.
uint32_t row_max_n_words;

// storage location for the list of key to max atom maps
key_to_max_atoms_map** keys_to_max_atoms;

// tracker for length of the key to max atoms map
uint32_t n_keys_to_max_atom_map = 0;

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
    address_t core_address = data_specification_get_data_address();

    master_pop_base_address = data_specification_get_region(
        POPULATION_TABLE_REGION, core_address);
    synaptic_matrix_base_address = data_specification_get_region(
        SYNAPTIC_MATRIX_REGION, core_address);
    bit_field_base_address = data_specification_get_region(
        BIT_FIELD_FILTER_REGION, core_address);
    direct_matrix_region_base_address = data_specification_get_region(
        DIRECT_MATRIX_REGION, core_address);
    bit_field_builder_base_address = data_specification_get_region(
        BIT_FIELD_BUILDER, core_address);

    // printer
    log_debug("master_pop_table_base_address = %0x", master_pop_base_address);
    log_debug(
        "synaptic_matrix_base_address = %0x", synaptic_matrix_base_address);
    log_debug("bit_field_base_address = %0x", bit_field_base_address);
    log_debug("direct_matrix_region_base_address = %0x",
              direct_matrix_region_base_address);
    log_debug("bit_field_builder = %0x", bit_field_builder_base_address);
    log_info("finished reading in vertex data region addresses");
}


void _read_in_the_key_to_max_atom_map(){

    // allocate dtcm for the key to max atom map
    uint32_t position_in_sdram_init_data = 0;
    n_keys_to_max_atom_map =
        bit_field_builder_base_address[position_in_sdram_init_data];
    log_info(" n keys to max atom map entries is %d",
             n_keys_to_max_atom_map);
    position_in_sdram_init_data += 1;

    keys_to_max_atoms = spin1_malloc(
        sizeof(key_to_max_atoms_map*) * n_keys_to_max_atom_map);

    if (keys_to_max_atoms == NULL){
        log_error("failed to allocate dtcm for the key to max atom map");
        rt_error(RTE_ABORT);
    }

    // put map into dtcm
    for (uint32_t key_to_max_atom_index = 0;
            key_to_max_atom_index < n_keys_to_max_atom_map;
            key_to_max_atom_index++){

        // allocate dtcm for region struct.
        keys_to_max_atoms[key_to_max_atom_index] =
            (key_to_max_atoms_map *) spin1_malloc(
                sizeof(key_to_max_atoms_map));

        // check dtcm was allocated
        if (keys_to_max_atoms[key_to_max_atom_index] == NULL){
            log_error("cant allocate dtcm for key to max atom %d regions",
                      key_to_max_atom_index);
            rt_error(RTE_ABORT);
        }

        spin1_memcpy(
            keys_to_max_atoms[key_to_max_atom_index],
            &bit_field_builder_base_address[position_in_sdram_init_data],
            sizeof(key_to_max_atoms_map));
        position_in_sdram_init_data +=
            sizeof(key_to_max_atoms_map) / BYTE_TO_WORD_CONVERSION;

        // print
        log_debug("entry %d has key %d and n_atoms of %d",
            key_to_max_atom_index,
            keys_to_max_atoms[key_to_max_atom_index]->key,
            keys_to_max_atoms[key_to_max_atom_index]->n_atoms);
    }
    log_info("finished reading in key to max atom map");
}


//! \brief deduces n neurons from the key
//! \param[in] mask: the key to convert to n_neurons
//! \return the number of neurons from the key map based off this key
uint32_t _n_neurons_from_key(uint32_t key){
    uint32_t key_index = 0;
    while (key_index < n_keys_to_max_atom_map){
        key_to_max_atoms_map* entry = keys_to_max_atoms[key_index];
        if (entry->key == key){
            return entry->n_atoms;
        }
        key_index ++;
    }
    log_error("didnt find the key %d in the map. WTF!", key);
    rt_error(RTE_ABORT);
    return NULL;
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
        uint32_t key = population_table_get_spike_for_index(master_pop_entry);
        uint32_t n_neurons = _n_neurons_from_key(key);
        log_debug("entry %d, key = %0x, n_neurons = %d",
                  master_pop_entry, key, n_neurons);

        // generate the bitfield for this master pop entry
        uint32_t n_words = get_bit_field_size(n_neurons);

        log_debug("n neurons is %d. n words is %d", n_neurons, n_words);
        fake_bit_fields[master_pop_entry] = bit_field_alloc(n_neurons);
        if (fake_bit_fields[master_pop_entry] == NULL){
            log_error("could not allocate %d bytes of dtcm for bit field",
                      n_words * sizeof(uint32_t));
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
        log_debug("\n\nfield for index %d", bit_field_index);
        bit_field_t field = (bit_field_t) fake_bit_fields[bit_field_index];
        uint32_t key = population_table_get_spike_for_index(bit_field_index);
        uint32_t n_neurons = _n_neurons_from_key(key);
        for (uint32_t neuron_id = 0; neuron_id < n_neurons; neuron_id ++){
            if (bit_field_test(field, neuron_id)){
                log_debug("neuron id %d was set", neuron_id);
            }
            else{
                log_debug("neuron id %d was not set", neuron_id);
            }
        }
    }
    log_debug("finished bit field print");
}

//! \brief sets up the master pop table and synaptic matrix for the bit field
//!        processing
//! \return: bool that states if the init was successful or not.
bool initialise(){

    // init the synapses to get direct synapse address
    log_info("direct synapse init");
    if (!direct_synapses_initialise(
            direct_matrix_region_base_address, &direct_synapses_address)) {
        log_error("failed to init the synapses. failing");
        return false;
    }

    // init the master pop table
    log_info("pop table init");
    if (!population_table_initialise(
            master_pop_base_address, synaptic_matrix_base_address,
            direct_synapses_address, &row_max_n_words)) {
        log_error("failed to init the master pop table. failing");
        return false;
    }

    log_info(" elements in master pop table is %d \n and max rows is %d",
             population_table_length(), row_max_n_words);

    // read in the correct key to max atom map
    _read_in_the_key_to_max_atom_map();

    // set up a fake bitfield so that it always says there's something to read
    if (!_create_fake_bit_field()){
        log_error("failed to create fake bit field");
        return false;
    }

    // print fake bitfield
    //_print_fake_bit_field();

    // set up a sdram read for a row
    log_info("allocating dtcm for row data");
    row_data = spin1_malloc(row_max_n_words * sizeof(uint32_t));
    if (row_data == NULL){
        log_error("could not allocate dtcm for the row data");
        return false;
    }
    log_debug("finished dtcm for row data");
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
    if (synapse_row_plastic_size(row) > 0){
        log_debug("plastic row had entries, so cant be pruned");
        return true;
    }
    else{
        // Get address of non-plastic region from row
        address_t fixed_region_address = synapse_row_fixed_region(row);
        uint32_t fixed_synapse =
            synapse_row_num_fixed_synapses(fixed_region_address);
        if (fixed_synapse == 0){
            log_debug(
                "plastic and fixed do not have entries, so can be pruned");
            return false;
        }
        else{
            log_debug("fixed row has entries, so cant be pruned");
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
    log_debug("process synaptic row");
    return process_synaptic_row(row_data);
}

//! \brief creates the bitfield for this master pop table and synaptic matrix
//! \param[in] vertex_id: the index in the regions.
//! \return bool that states if it was successful at generating the bitfield
bool generate_bit_field(){

    // write how many entries (thus bitfields) are to be generated into sdram

    uint32_t position = 0;
    log_debug("mem cpy for pop length");
    bit_field_base_address[position] = population_table_length();
    log_debug("update position");
    position ++;

    // iterate through the master pop entries
    log_debug("starting master pop entry bit field generation");
    for (uint32_t master_pop_entry=0;
            master_pop_entry < population_table_length();
            master_pop_entry++){

        // determine keys masks and n_neurons
        spike_t key = population_table_get_spike_for_index(master_pop_entry);
        uint32_t mask = population_table_get_mask_for_entry(master_pop_entry);
        uint32_t n_neurons = _n_neurons_from_key(key);

        // generate the bitfield for this master pop entry
        uint32_t n_words = get_bit_field_size(n_neurons);

        log_debug("pop entry %d, key = %d, mask = %0x, n_neurons = %d",
                  master_pop_entry, (uint32_t) key, mask, n_neurons);
        bit_field_t bit_field = bit_field_alloc(n_neurons);
        if (bit_field == NULL){
            log_error("could not allocate dtcm for bit field");
            return false;
        }

        // set the bitfield to 0. so assuming a miss on everything
        clear_bit_field(bit_field, n_words);
        log_debug("cleared bit field");

        // update sdram with size of this bitfield
        bit_field_base_address[position] = key;
        log_debug("putting master pop key %d in position %d", key, position);
        bit_field_base_address[position + 1] = n_words;
        log_debug("putting n words %d in position %d", n_words, position + 1);
        position += 2;

        // iterate through neurons and ask for rows from master pop table
        log_debug("searching neuron ids");
        for (uint32_t neuron_id =0; neuron_id < n_neurons; neuron_id++){

            // update key with neuron id
            spike_t new_key = (spike_t) (key + neuron_id);
            log_debug("new key for neurons %d is %0x", neuron_id, new_key);

            // holder for the bytes to transfer if we need to read sdram.
            size_t n_bytes_to_transfer;
            if (population_table_get_first_address(
                    new_key, &row_address, &n_bytes_to_transfer)){

                log_debug("after got address");
                // This is a direct row to process, so will have 1 target, so
                // no need to go further
                if (n_bytes_to_transfer == 0) {
                    log_debug("direct synapse");
                    bit_field_set(bit_field, neuron_id);
                } else {
                    // sdram read (faking dma transfer)
                    log_debug("dma read synapse");
                    if (_do_sdram_read_and_test(
                            row_address, n_bytes_to_transfer)){
                        bit_field_set(bit_field, neuron_id);
                    }
                }
            }
            else{
                log_error("should never get here!!! As this would imply a "
                          "master pop entry which has no master pop entry. "
                          "if this is true for all atoms. Would indicate a "
                          "prunable edge");
            }
            // if returned false, then the bitfield should be set to 0.
            // Which its by default already set to. so do nothing. so no else.
        }

        // write bitfield to sdram.
        log_debug("writing bitfield to sdram for core use");
        log_debug("writing to address %0x, %d words to write",
                 &bit_field_base_address[position], n_words);
        spin1_memcpy(&bit_field_base_address[position], bit_field,
                     n_words * BYTE_TO_WORD_CONVERSION);
        position += n_words;

        // free dtcm of bitfield.
        log_debug("freeing the bitfield dtcm");
        sark_free(bit_field);
    }
    return true;
}

void c_main(void) {
    // set to running state
    sark_cpu_state(CPU_STATE_RUN);

    log_info("starting the bit field expander");

    // read in sdram data
    read_in_addresses();

    // generate bit field for each vertex regions
    if (!initialise()){
        log_error("failed to init the master pop and synaptic matrix");
        rt_error(RTE_ABORT);
    }
    log_info("generating bit field");
    if (!generate_bit_field()){
        log_error("failed to generate bitfield");
        rt_error(RTE_ABORT);
    };

    log_info("successfully processed the bitfield");

}
