#ifndef _SP_STRUCTS_H_
#define _SP_STRUCTS_H_

#include <neuron/synapse_row.h>
#include <random.h>

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
        machine_no_atoms, low_atom, high_atom,
        size_ff_prob, size_lat_prob, grid_x, grid_y, p_elim_dep, p_elim_pot;
    // the 2 seeds that are used: shared for sync, local for everything else
    mars_kiss64_seed_t shared_seed, local_seed;
    // information about all pre-synaptic sub-populations eligible for rewiring
    pre_pop_info_table_t pre_pop_info_table;
    // distance dependent probabilities LUTs
    uint16_t *ff_probabilities, *lat_probabilities;
    // inverse of synaptic matrix
    int32_t *post_to_pre_table;
    // flags for synapse type of lateral connections and whether formations
    // sample randomly from all available neurons
    int32_t lateral_inhibition, random_partner, is_distance_dependent;
} rewiring_data_t;

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

#endif // _SP_STRUCTS_H_
