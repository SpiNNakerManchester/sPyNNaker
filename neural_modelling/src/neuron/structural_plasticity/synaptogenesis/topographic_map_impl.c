/*! \file
 *
 * SUMMARY
 *  \brief This file contains the main functions for probabilistic
 *  synaptogenesis.
 *
 * Author: Petrut Bogdan
 *
 */
#include <neuron/structural_plasticity/synaptogenesis_dynamics.h>
#include <neuron/population_table/population_table.h>

#include <random.h>
#include <spin1_api.h>
#include <debug.h>
#include <stdfix-full-iso.h>

#include <neuron/synapse_row.h>

#include <neuron/synapses.h>
#include <neuron/plasticity/synapse_dynamics.h>

#include <common/maths-util.h>
#include <neuron/structural_plasticity/sp_structs.h>
#include <simulation.h>

// (Potential) Presynaptic partner selection
#include "partner_selection/partner.h"

//-----------------------------------------------------------------------------
// Structures and global data                                                 |
//-----------------------------------------------------------------------------
// DMA tags
#define DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING 5
#define DMA_TAG_WRITE_SYNAPTIC_ROW_AFTER_REWIRING 7

#define MAX_SHORT 65535
#define IS_CONNECTION_LAT 1

// the instantiation of the previous struct
rewiring_data_t rewiring_data;

//! struct representing the current state of rewiring
typedef struct {
    // what synaptic row are we servicing?
    address_t sdram_synaptic_row;
    // what are the currently selecting pre- and post-synaptic neurons and
    // what is the distance between them
    uint32_t pre_syn_id, post_syn_id, distance;
    // data structure to pass back weight, delay and offset information from
    // static synapses / stdp synapses
    structural_plasticity_data_t sp_data;
    // what is the current time
    uint32_t current_time;
    // what is the current control word
    int16_t current_controls;
    int32_t connection_type;
    // what are the global pre- and post-synaptic neuron IDs
    uint32_t global_pre_syn_id, global_post_syn_id;
    // does the post to pre table have contain a connection for the selected
    // slot
    bool element_exists;
    // information extracted from the post to pre table
    uint32_t offset_in_table, pop_index, subpop_index, neuron_index;
} current_state_t;

// instantiation of the previous struct
current_state_t current_state;


//! abs function
static int my_abs(int a) {
    return a < 0 ? -a : a;
}

//! function to unpack element from post to pre table into constituent bits
static inline bool unpack_post_to_pre(
    int32_t value, uint32_t* pop_index,
    uint32_t* subpop_index, uint32_t* neuron_index)
{
    if (value == -1) {
        return false;
    }
    *neuron_index = (value      ) & 0xFFFF;
    *subpop_index = (value >> 16) & 0xFF;
    *pop_index    = (value >> 24) & 0xFF;
    return true;
}

//! opposite function of unpack. packs up different bits into a word to be
//! placed into the post to pre table
static inline int pack(
    uint32_t pop_index, uint32_t subpop_index, uint32_t neuron_index)
{
    uint32_t value, masked_pop_index, masked_subpop_index, masked_neuron_index;
    masked_pop_index    = pop_index    & 0xFF;
    masked_subpop_index = subpop_index & 0xFF;
    masked_neuron_index = neuron_index & 0xFFFF;
    value = (masked_pop_index << 24) |
            (masked_subpop_index << 16) |
             masked_neuron_index;
    return (int) value;
}

//-----------------------------------------------------------------------------
// Initialisation                                                             |
//-----------------------------------------------------------------------------

//! \brief Initialisation of synaptic rewiring (synaptogenesis)
//! parameters (random seed, spread of receptive field etc.)
//! \param[in] sdram_sp_address Address of the start of the SDRAM region
//! which contains synaptic rewiring params.
//! \return address_t Address after the final word read from SDRAM.
address_t synaptogenesis_dynamics_initialise(address_t sdram_sp_address)
{
    log_info("SR init.");
    // Read in all of the parameters from SDRAM
    int32_t *sp_word = (int32_t *) sdram_sp_address;
    rewiring_data.fast = *sp_word++;
    rewiring_data.p_rew = *sp_word++;
    rewiring_data.s_max = *sp_word++;
    rewiring_data.lateral_inhibition = *sp_word++;
    rewiring_data.random_partner = *sp_word++;
    rewiring_data.is_distance_dependent = *sp_word++;

    rewiring_data.app_no_atoms = *sp_word++;
    rewiring_data.low_atom = *sp_word++;
    rewiring_data.high_atom = *sp_word++;
    rewiring_data.machine_no_atoms = *sp_word++;

    rewiring_data.grid_x = *sp_word++;
    rewiring_data.grid_y = *sp_word++;

    rewiring_data.p_elim_dep = *sp_word++;
    rewiring_data.p_elim_pot = *sp_word++;

    rewiring_data.shared_seed[0] = *sp_word++;
    rewiring_data.shared_seed[1] = *sp_word++;
    rewiring_data.shared_seed[2] = *sp_word++;
    rewiring_data.shared_seed[3] = *sp_word++;

    rewiring_data.local_seed[0] = *sp_word++;
    rewiring_data.local_seed[1] = *sp_word++;
    rewiring_data.local_seed[2] = *sp_word++;
    rewiring_data.local_seed[3] = *sp_word++;

    rewiring_data.pre_pop_info_table.no_pre_pops = *sp_word++;

    // Need to malloc space for subpop_info, i.e. an array
    // containing information for each pre-synaptic application vertex
    if (!rewiring_data.pre_pop_info_table.no_pre_pops) {
        return NULL;
    }
    rewiring_data.pre_pop_info_table.subpop_info = sark_alloc(
        rewiring_data.pre_pop_info_table.no_pre_pops,
        sizeof(subpopulation_info_t));

    uint32_t index;
    uint16_t *half_word;
    for (index = 0;
            index < rewiring_data.pre_pop_info_table.no_pre_pops;
            index ++) {
        subpopulation_info_t *subpopinfo =
            &rewiring_data.pre_pop_info_table.subpop_info[index];

        // Read the actual number of presynaptic sub-populations
        half_word = (uint16_t *) sp_word;
        subpopinfo->no_pre_vertices = *half_word++;
        subpopinfo->sp_control = *half_word++;
        subpopinfo->delay_lo = *half_word++;
        subpopinfo->delay_hi = *half_word++;
        log_info("delays  [%d, %d]", subpopinfo->delay_lo, subpopinfo->delay_hi);
        sp_word = (int32_t *) half_word;
        subpopinfo->weight = *sp_word++;
        log_info("weight %d", subpopinfo->weight);
        subpopinfo->connection_type = *sp_word++;
        log_info("syn_type %d", subpopinfo->connection_type);
        subpopinfo->total_no_atoms = *sp_word++;
        subpopinfo->key_atom_info = sark_alloc(
            subpopinfo->no_pre_vertices, sizeof(key_atom_info_t));
        int32_t subpop_index;
        for (subpop_index = 0;
                subpop_index < subpopinfo->no_pre_vertices;
                subpop_index++) {
            // key
            subpopinfo->key_atom_info[subpop_index].key = *sp_word++;
            // n_atoms
            subpopinfo->key_atom_info[subpop_index].n_atoms = *sp_word++;
            // lo_atom
            subpopinfo->key_atom_info[subpop_index].lo_atom = *sp_word++;
            // mask
            subpopinfo->key_atom_info[subpop_index].mask = *sp_word++;
        }
    }

    // Read the probability vs. distance tables into DTCM
    rewiring_data.size_ff_prob = *sp_word++;
    rewiring_data.ff_probabilities = sark_alloc(
        rewiring_data.size_ff_prob, sizeof(uint16_t));
    half_word = (uint16_t *) sp_word;
    for (index = 0; index < rewiring_data.size_ff_prob; index++) {
        rewiring_data.ff_probabilities[index] = *half_word++;
    }

    sp_word = (int32_t *) half_word;
    rewiring_data.size_lat_prob = *sp_word++;

    rewiring_data.lat_probabilities = sark_alloc(
        rewiring_data.size_lat_prob, sizeof(uint16_t));

    half_word = (uint16_t *) sp_word;
    for (index = 0; index < rewiring_data.size_lat_prob; index++) {
        rewiring_data.lat_probabilities[index] = *half_word++;
    }

    assert(((int) half_word) % 4 == 4);

    sp_word = (int32_t *) half_word;

    // Setting up Post to Pre table
    rewiring_data.post_to_pre_table = sp_word;
    int total_no_of_elements = rewiring_data.s_max *
        rewiring_data.machine_no_atoms;
    sp_word = &rewiring_data.post_to_pre_table[total_no_of_elements + 1];

    // Setting up RNG
    validate_mars_kiss64_seed(rewiring_data.shared_seed);
    // Setting up local RNG
    validate_mars_kiss64_seed(rewiring_data.local_seed);

    log_debug("SR init complete.");
    return (address_t) sp_word;
}

bool synaptogenesis_dynamics_rewire(
        uint32_t time, spike_t *spike, address_t *synaptic_row_address,
        uint32_t *n_bytes) {
    current_state.current_time = time;

    // Randomly choose a postsynaptic (application neuron)
    uint32_t post_id;
    post_id = ulrbits(mars_kiss64_seed(rewiring_data.shared_seed)) *
        rewiring_data.app_no_atoms;

    // Check if neuron is in the current machine vertex
    if (post_id < rewiring_data.low_atom ||
        post_id > rewiring_data.high_atom) {
        return false;
    }
    post_id -= rewiring_data.low_atom;

    uint32_t pre_app_pop = 0, pre_sub_pop = 0, choice = 0;
    bool element_exists = false;

    // Select an arbitrary synaptic element for the neurons
    uint row_offset, column_offset;
    row_offset = post_id * rewiring_data.s_max;
    column_offset = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
        rewiring_data.s_max;
    uint total_offset = row_offset + column_offset;
    int value = rewiring_data.post_to_pre_table[total_offset];
    current_state.offset_in_table = total_offset;

    element_exists = unpack_post_to_pre(value, &pre_app_pop,
        &pre_sub_pop, &choice);

    current_state.element_exists = element_exists;
    if (!element_exists) {
        if (!potential_presynaptic_partner(&rewiring_data, &pre_app_pop,
                &pre_sub_pop, &choice, spike)) {
            return false;
        }
    } else if (!element_exists && rewiring_data.random_partner) {
        pre_app_pop = ulrbits(mars_kiss64_seed(rewiring_data.local_seed))
                    * rewiring_data.pre_pop_info_table.no_pre_pops;
        subpopulation_info_t *preapppop_info =
            &rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop];

        // Select presynaptic sub-population
        choice = ulrbits(mars_kiss64_seed(rewiring_data.local_seed))
                    * preapppop_info->total_no_atoms;
        uint32_t sum = 0;
        int i;
        for (i=0; i < preapppop_info->no_pre_vertices; i++) {
            sum += preapppop_info->key_atom_info[i].n_atoms;
            if (sum >= choice) {
                break;
            }
        }
        pre_sub_pop = i;

        // Select a presynaptic neuron ID
        choice = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
            preapppop_info->key_atom_info[pre_sub_pop].n_atoms;

        *spike = preapppop_info->key_atom_info[pre_sub_pop].key | choice;
    } else {
        *spike = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop]
                .key_atom_info[pre_sub_pop].key | choice;
    }

    if (!population_table_get_first_address(*spike, synaptic_row_address,
        n_bytes)) {
        log_error("FAIL@key %d", *spike);
        rt_error(RTE_SWERR);
    }

    // Saving current state
    current_state.pop_index = pre_app_pop;
    current_state.subpop_index = pre_sub_pop;
    current_state.neuron_index = choice;
    current_state.sdram_synaptic_row = synaptic_row_address;
    current_state.pre_syn_id = choice;
    current_state.post_syn_id = post_id;
    current_state.current_controls = rewiring_data.pre_pop_info_table
            .subpop_info[pre_app_pop].sp_control;
    current_state.connection_type = rewiring_data.pre_pop_info_table
            .subpop_info[pre_app_pop].connection_type;


    if (rewiring_data.is_distance_dependent) {
        // Compute distances
        // To do this I need to take the DIV and MOD of the
        // post-synaptic neuron ID, of the pre-synaptic neuron ID
        // Compute the distance of these 2 measures
        int32_t pre_x, pre_y, post_x, post_y, pre_global_id, post_global_id;
        // Pre computation requires querying the table with global information
        pre_global_id = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop]
                .key_atom_info[pre_sub_pop].lo_atom + current_state.pre_syn_id;
        post_global_id = current_state.post_syn_id + rewiring_data.low_atom;

        if (rewiring_data.grid_x > 1) {
            pre_x = pre_global_id / rewiring_data.grid_x;
            post_x = post_global_id / rewiring_data.grid_x;
        } else {
            pre_x = 0;
            post_x = 0;
        }

        if (rewiring_data.grid_y > 1) {
            pre_y = pre_global_id % rewiring_data.grid_y;
            post_y = post_global_id % rewiring_data.grid_y;
        } else {
            pre_y = 0;
            post_y = 0;
        }

        // With periodic boundary conditions
        uint delta_x, delta_y;
        delta_x = my_abs(pre_x - post_x);
        delta_y = my_abs(pre_y - post_y);

        if (delta_x > rewiring_data.grid_x >> 1 && rewiring_data.grid_x > 1) {
            delta_x -= rewiring_data.grid_x;
        }

        if (delta_y > rewiring_data.grid_y >> 1 && rewiring_data.grid_y > 1) {
            delta_y -= rewiring_data.grid_y;
        }

        current_state.distance = delta_x * delta_x + delta_y * delta_y;
        current_state.global_pre_syn_id = pre_global_id;
        current_state.global_post_syn_id = post_global_id;
    } // if the rewiring is distance dependent
    // else, skip

    return true;
}

//! \brief This function is a rewiring DMA callback
//! \param[in] dma_id: the ID of the DMA
//! \param[in] dma_tag: the DMA tag, i.e. the tag used for reading row for
//!                     rewiring
//! \return nothing
bool synaptogenesis_row_restructure(uint32_t time, address_t row) {
    // the selected pre- and postsynaptic IDs are in current_state

    // find the offset of the neuron in the current row
    bool search_hit = synapse_dynamics_find_neuron(
        current_state.post_syn_id, row,
        &(current_state.sp_data.weight), &(current_state.sp_data.delay),
        &(current_state.sp_data.offset));

    if (current_state.element_exists && search_hit) {
        return synaptogenesis_dynamics_elimination_rule(time, row);
    } else {
        return synaptogenesis_dynamics_formation_rule(time, row);
    }
}

//! \brief Formation and elimination are structurally agnostic, i.e. they don't
//! care how synaptic rows are organised in physical memory.
//!
//!  As such, they need to call functions that have a knowledge of how the
//!  memory is physically organised to be able to modify Plastic-Plastic
//!  synaptic regions.
//!
//!  The elimination rule calls the remove neuron function in the appropriate
//!  module (STDP or static).
//!  \return true if elimination was successful
bool synaptogenesis_dynamics_elimination_rule(uint32_t time, address_t row)
{
    // Is synaptic weight <.5 g_max? (i.e. synapse is depressed)
    uint32_t r = mars_kiss64_seed(rewiring_data.local_seed);

    // get projection-specific weight from pop sub-population info table
    int appr_scaled_weight = rewiring_data.pre_pop_info_table
            .subpop_info[current_state.pop_index].weight;
    if (current_state.sp_data.weight < (appr_scaled_weight / 2) &&
            r > rewiring_data.p_elim_dep) {
        return false;
    }

    // otherwise, if synapse is potentiated, use probability 2
    if (current_state.sp_data.weight >= (appr_scaled_weight / 2) &&
            r > rewiring_data.p_elim_pot) {
        return false;
    }
    if (!synapse_dynamics_remove_neuron(current_state.sp_data.offset, row)) {
        return false;
    }
    rewiring_data.post_to_pre_table[current_state.offset_in_table] = -1;
    return true;
}

//! \brief Formation and elimination are structurally agnostic, i.e. they don't
//! care how synaptic rows are organised in physical memory.
//!
//!  As such, they need to call functions that have a knowledge of how the
//!  memory is physically organised to be able to modify Plastic-Plastic
//!  synaptic regions.
//!
//!  The formation rule calls the add neuron function in the appropriate
//!  module (STDP or static).
//!  \return true if formation was successful
bool synaptogenesis_dynamics_formation_rule(uint32_t time, address_t row) {
    // Distance based probability extracted from the appropriate LUT
    uint16_t probability;
    uint no_elems = synapse_dynamics_n_connections_in_row(
        synapse_row_fixed_region(row));
    if (no_elems >= rewiring_data.s_max) {
        log_debug("row is full");
        return false;
    }

    if (rewiring_data.is_distance_dependent) {
        if ((!(current_state.current_controls & IS_CONNECTION_LAT) &&
            current_state.distance > rewiring_data.size_ff_prob)
            || ((current_state.current_controls & IS_CONNECTION_LAT) &&
                current_state.distance > rewiring_data.size_lat_prob)) {
            return false;
        }

    } // if the rewiring is distance dependent

    if (!(current_state.current_controls & IS_CONNECTION_LAT)) {
        probability = rewiring_data.ff_probabilities[current_state.distance];
    } else {
        probability = rewiring_data.lat_probabilities[current_state.distance];
    }
    uint16_t r = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) * MAX_SHORT;
    if (r > probability) {
        return false;
    }
    // else, skip
    int appr_scaled_weight = rewiring_data.pre_pop_info_table
            .subpop_info[current_state.pop_index].weight;

    uint  actual_delay;
    int offset = rewiring_data.pre_pop_info_table
            .subpop_info[current_state.pop_index].delay_hi -
            rewiring_data.pre_pop_info_table
            .subpop_info[current_state.pop_index].delay_lo;
    actual_delay = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
        offset + rewiring_data.pre_pop_info_table
            .subpop_info[current_state.pop_index].delay_lo;

    if (!synapse_dynamics_add_neuron(
            current_state.post_syn_id, row,
            appr_scaled_weight, actual_delay,
            current_state.connection_type)) {
        return false;
    }

    int the_pack = pack(current_state.pop_index,
        current_state.subpop_index,
        current_state.neuron_index);
    rewiring_data.post_to_pre_table[current_state.offset_in_table] = the_pack;
    return true;
}

//! retrieve the period of rewiring
//! based on is_fast(), this can either mean how many times rewiring happens
//! in a timestep, or how many timesteps have to pass until rewiring happens.
int32_t synaptogenesis_rewiring_period(void) {
    return rewiring_data.p_rew;
}

//! controls whether rewiring is attempted multiple times per timestep
//! or after a number of timesteps.
bool synaptogenesis_is_fast(void) {
    return rewiring_data.fast == 1;
}
