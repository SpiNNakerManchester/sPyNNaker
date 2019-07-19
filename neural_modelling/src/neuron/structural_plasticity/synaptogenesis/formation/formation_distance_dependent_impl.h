#ifndef _FORMATION_DISTANCE_DEPENDENT_H_
#define _FORMATION_DISTANCE_DEPENDENT_H_

#include "formation.h"

#define MAX_SHORT 65535

typedef struct formation_params {
    uint32_t grid_x;
    uint32_t grid_y;
    uint32_t ff_prob_size;
    uint32_t lat_prob_size;
    uint16_t prob_tables[];
} formation_params;

extern formation_params *form_params;
extern uint16_t *ff_probs;
extern uint16_t *lat_probs;


//! abs function
static int my_abs(int a) {
    return a < 0 ? -a : a;
}

static inline bool synaptogenesis_formation_rule(rewiring_data_t *rewiring_data,
        current_state_t *current_state, uint32_t time, address_t row) {
    use(time);

    // Compute distances
    // To do this I need to take the DIV and MOD of the
    // post-synaptic neuron ID, of the pre-synaptic neuron ID
    // Compute the distance of these 2 measures
    int32_t pre_x, pre_y, post_x, post_y, pre_global_id, post_global_id;
    // Pre computation requires querying the table with global information
    pre_global_id = rewiring_data->pre_pop_info_table.subpop_info[current_state->pop_index]
            .key_atom_info[current_state->subpop_index].lo_atom + current_state->pre_syn_id;
    post_global_id = current_state->post_syn_id + rewiring_data->low_atom;

    if (formation_params->grid_x > 1) {
        pre_x = pre_global_id / formation_params->grid_x;
        post_x = post_global_id / formation_params->grid_x;
    } else {
        pre_x = 0;
        post_x = 0;
    }

    if (formation_params->grid_y > 1) {
        pre_y = pre_global_id % formation_params->grid_y;
        post_y = post_global_id % formation_params->grid_y;
    } else {
        pre_y = 0;
        post_y = 0;
    }

    // With periodic boundary conditions
    uint delta_x, delta_y;
    delta_x = my_abs(pre_x - post_x);
    delta_y = my_abs(pre_y - post_y);

    if (delta_x > formation_params->grid_x >> 1 && formation_params->grid_x > 1) {
        delta_x -= formation_params->grid_x;
    }

    if (delta_y > formation_params->grid_y >> 1 && formation_params->grid_y > 1) {
        delta_y -= formation_params->grid_y;
    }

    uint32_t distance = delta_x * delta_x + delta_y * delta_y;

    // Distance based probability extracted from the appropriate LUT
    uint16_t probability;

    if ((!(current_state->current_controls & IS_CONNECTION_LAT) &&
            distance > formation_params->ff_prob_size)
        || ((current_state->current_controls & IS_CONNECTION_LAT) &&
            distance > formation_params->lat_prob_size)) {
        return false;
    }

    if (!(current_state->current_controls & IS_CONNECTION_LAT)) {
        probability = ff_probs[distance];
    } else {
        probability = lat_probs[distance];
    }
    uint16_t r = ulrbits(mars_kiss64_seed(rewiring_data->local_seed)) * MAX_SHORT;
    if (r > probability) {
        return false;
    }
    // else, skip

    return sp_structs_add_synapse(rewiring_data, current_state, row);
}

#endif // _FORMATION_DISTANCE_DEPENDENT_H_
