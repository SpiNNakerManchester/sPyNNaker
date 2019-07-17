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

#include <common/maths-util.h>
#include <neuron/structural_plasticity/sp_structs.h>
#include <simulation.h>

// Interface for rules
#include "partner_selection/partner.h"
#include "elimination/elimination.h"
#include "formation/formation.h"

//-----------------------------------------------------------------------------
// Structures and global data                                                 |
//-----------------------------------------------------------------------------

// the instantiation of the previous struct
rewiring_data_t rewiring_data;

// instantiation of the previous struct
current_state_t current_state;


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
    address_t addr = (address_t) sp_word;
    addr = partner_init(addr);
    addr = synaptogenesis_formation_init(addr);
    addr = synaptogenesis_elimination_init(addr);
    return (address_t) sp_word;
}

bool synaptogenesis_dynamics_rewire(
        uint32_t time, spike_t *spike, address_t *synaptic_row_address,
        uint32_t *n_bytes) {

    // Randomly choose a postsynaptic (application neuron)
    uint32_t post_id = ulrbits(mars_kiss64_seed(rewiring_data.shared_seed)) *
        rewiring_data.app_no_atoms;

    // Check if neuron is in the current machine vertex
    if (post_id < rewiring_data.low_atom ||
        post_id > rewiring_data.high_atom) {
        return false;
    }
    post_id -= rewiring_data.low_atom;

    // Select an arbitrary synaptic element for the neurons
    uint row_offset = post_id * rewiring_data.s_max;
    uint column_offset = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
        rewiring_data.s_max;
    uint total_offset = row_offset + column_offset;
    int value = rewiring_data.post_to_pre_table[total_offset];
    current_state.offset_in_table = total_offset;

    uint32_t pre_app_pop = 0, pre_sub_pop = 0, neuron_id = 0;
    bool element_exists = unpack_post_to_pre(value, &pre_app_pop,
        &pre_sub_pop, &neuron_id);

    current_state.element_exists = element_exists;
    if (!element_exists) {
        if (!potential_presynaptic_partner(time, &rewiring_data, &pre_app_pop,
                &pre_sub_pop, &neuron_id, spike)) {
            return false;
        }
    } else {
        *spike = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop]
                .key_atom_info[pre_sub_pop].key | neuron_id;
    }

    if (!population_table_get_first_address(*spike, synaptic_row_address, n_bytes)) {
        log_error("FAIL@key %d", *spike);
        rt_error(RTE_SWERR);
    }

    // Saving current state
    current_state.pop_index = pre_app_pop;
    current_state.subpop_index = pre_sub_pop;
    current_state.neuron_index = neuron_id;
    current_state.pre_syn_id = neuron_id;
    current_state.post_syn_id = post_id;
    current_state.current_controls = rewiring_data.pre_pop_info_table
            .subpop_info[pre_app_pop].sp_control;
    current_state.connection_type = rewiring_data.pre_pop_info_table
            .subpop_info[pre_app_pop].connection_type;

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
        return synaptogenesis_elimination_rule(
            &rewiring_data, &current_state, time, row);
    } else {
        // Can't form if the row is full
        uint no_elems = synapse_dynamics_n_connections_in_row(
            synapse_row_fixed_region(row));
        if (no_elems >= rewiring_data.s_max) {
            log_debug("row is full");
            return false;
        }
        return synaptogenesis_formation_rule(
            &rewiring_data, &current_state, time, row);
    }
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

void synaptogenesis_spike_received(uint32_t time, spike_t spike) {
    partner_spike_received(time, spike);
}
