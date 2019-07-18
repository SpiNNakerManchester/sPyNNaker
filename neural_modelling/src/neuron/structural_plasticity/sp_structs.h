#ifndef _SP_STRUCTS_H_
#define _SP_STRUCTS_H_

#include <neuron/plasticity/synapse_dynamics.h>
#include <neuron/synapse_row.h>
#include <random.h>

#define IS_CONNECTION_LAT 1

typedef struct {
    weight_t weight;
    uint32_t delay;
    uint32_t offset;
} structural_plasticity_data_t;

//! information per atom
typedef struct {
    uint32_t key;
    uint32_t n_atoms;
    uint32_t lo_atom;
    uint32_t mask;
} key_atom_info_t;

//! individual pre-synaptic sub-population information
typedef struct {
    uint16_t no_pre_vertices;
    int16_t sp_control;
    int16_t delay_lo, delay_hi;
    uint32_t weight;
    uint32_t connection_type;
    int32_t total_no_atoms;
    key_atom_info_t *key_atom_info;
} subpopulation_info_t;

//! table of individual pre-synaptic information
typedef struct {
    uint32_t no_pre_pops;
    subpopulation_info_t *subpop_info;
} pre_pop_info_table_t;

//! parameters of the synaptic rewiring model
typedef struct {
    uint32_t p_rew, fast, s_max, app_no_atoms,
        machine_no_atoms, low_atom, high_atom;
    // the 2 seeds that are used: shared for sync, local for everything else
    mars_kiss64_seed_t shared_seed, local_seed;
    // information about all pre-synaptic sub-populations eligible for rewiring
    pre_pop_info_table_t pre_pop_info_table;
    // inverse of synaptic matrix
    int32_t *post_to_pre_table;
} rewiring_data_t;

//! function to unpack element from post to pre table into constituent bits
static inline bool unpack_post_to_pre(int32_t value, uint32_t* pop_index,
        uint32_t* subpop_index, uint32_t* neuron_index) {
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
static inline int pack(uint32_t pop_index, uint32_t subpop_index,
        uint32_t neuron_index) {
    uint32_t value, masked_pop_index, masked_subpop_index, masked_neuron_index;
    masked_pop_index    = pop_index    & 0xFF;
    masked_subpop_index = subpop_index & 0xFF;
    masked_neuron_index = neuron_index & 0xFFFF;
    value = (masked_pop_index << 24) |
            (masked_subpop_index << 16) |
             masked_neuron_index;
    return (int) value;
}

//! struct representing the current state of rewiring
typedef struct {
    // what are the currently selecting pre- and post-synaptic neurons
    uint32_t pre_syn_id, post_syn_id;
    // data structure to pass back weight, delay and offset information from
    // static synapses / stdp synapses
    structural_plasticity_data_t sp_data;
    // what is the current control word
    int16_t current_controls;
    int32_t connection_type;
    // does the post to pre table have contain a connection for the selected
    // slot
    bool element_exists;
    // information extracted from the post to pre table
    uint32_t offset_in_table, pop_index, subpop_index, neuron_index;
} current_state_t;

// \!brief unpack the spike into key and identifying information for the neuron;
//         Identify pop, sub-population and low and high atoms
static inline bool sp_structs_find_by_spike(
        rewiring_data_t *rewiring_data, spike_t spike, uint32_t *neuron_id,
        uint32_t *population_id, uint32_t *sub_population_id) {
    // Amazing linear search inc.
    // Loop over all populations
    for (uint32_t i = 0;
            i < rewiring_data->pre_pop_info_table.no_pre_pops; i++) {
        subpopulation_info_t pre_pop_info =
            rewiring_data->pre_pop_info_table.subpop_info[i];

        // Loop over all sub-populations and check if the KEY matches
        // (with neuron ID masked out)
        for (int subpop_index = 0;
                subpop_index < pre_pop_info.no_pre_vertices;
                subpop_index++) {
            key_atom_info_t *kai = &pre_pop_info.key_atom_info[subpop_index];
            if ((spike & kai->mask) == kai->key) {
                *population_id = i;
                *sub_population_id = subpop_index;
                *neuron_id = spike & ~kai->mask;
                return true;
            }
        }
    }
    return false;
}

// \brief Get the sub-population id and sub-population-based neuron id given
//        the population id and the population-based neuron id
static inline bool sp_structs_get_sub_pop_info(
        rewiring_data_t *rewiring_data, uint32_t population_id,
        uint32_t pop_neuron_id, uint32_t *sub_population_id,
        uint32_t *sub_pop_neuron_id, uint32_t *spike) {
    subpopulation_info_t app_pop_info =
        rewiring_data->pre_pop_info_table.subpop_info[population_id];
    uint32_t neuron_id = pop_neuron_id;
    for (uint32_t i = 0; i < app_pop_info.no_pre_vertices; i++) {
        uint32_t n_atoms = app_pop_info.key_atom_info[i].n_atoms;
        if (neuron_id < n_atoms) {
            *sub_population_id = i;
            *sub_pop_neuron_id = neuron_id;
            *spike = app_pop_info.key_atom_info[i].key | neuron_id;
            return true;
        }
        neuron_id -= n_atoms;
    }
    return false;
}

static inline bool sp_structs_remove_synapse(rewiring_data_t *rewiring_data,
        current_state_t *current_state, address_t row) {
    if (!synapse_dynamics_remove_neuron(current_state->sp_data.offset, row)) {
        return false;
    }
    rewiring_data->post_to_pre_table[current_state->offset_in_table] = -1;
    return true;
}

static inline bool sp_structs_add_synapse(rewiring_data_t *rewiring_data,
        current_state_t *current_state, address_t row) {
    int appr_scaled_weight = rewiring_data->pre_pop_info_table
            .subpop_info[current_state->pop_index].weight;

    uint actual_delay;
    int offset = rewiring_data->pre_pop_info_table
            .subpop_info[current_state->pop_index].delay_hi -
            rewiring_data->pre_pop_info_table
            .subpop_info[current_state->pop_index].delay_lo;
    actual_delay = ulrbits(mars_kiss64_seed(rewiring_data->local_seed)) *
        offset + rewiring_data->pre_pop_info_table
            .subpop_info[current_state->pop_index].delay_lo;

    if (!synapse_dynamics_add_neuron(
            current_state->post_syn_id, row,
            appr_scaled_weight, actual_delay,
            current_state->connection_type)) {
        return false;
    }

    int the_pack = pack(current_state->pop_index, current_state->subpop_index,
        current_state->neuron_index);
    rewiring_data->post_to_pre_table[current_state->offset_in_table] = the_pack;
    return true;

}

#endif // _SP_STRUCTS_H_
