#ifndef _FORMATION_DISTANCE_DEPENDENT_H_
#define _FORMATION_DISTANCE_DEPENDENT_H_

#include "formation.h"

#define MAX_SHORT 65535

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

    if (rewiring_data->grid_x > 1) {
        pre_x = pre_global_id / rewiring_data->grid_x;
        post_x = post_global_id / rewiring_data->grid_x;
    } else {
        pre_x = 0;
        post_x = 0;
    }

    if (rewiring_data->grid_y > 1) {
        pre_y = pre_global_id % rewiring_data->grid_y;
        post_y = post_global_id % rewiring_data->grid_y;
    } else {
        pre_y = 0;
        post_y = 0;
    }

    // With periodic boundary conditions
    uint delta_x, delta_y;
    delta_x = my_abs(pre_x - post_x);
    delta_y = my_abs(pre_y - post_y);

    if (delta_x > rewiring_data->grid_x >> 1 && rewiring_data->grid_x > 1) {
        delta_x -= rewiring_data->grid_x;
    }

    if (delta_y > rewiring_data->grid_y >> 1 && rewiring_data->grid_y > 1) {
        delta_y -= rewiring_data->grid_y;
    }

    uint32_t distance = delta_x * delta_x + delta_y * delta_y;

    // Distance based probability extracted from the appropriate LUT
    uint16_t probability;

    if ((!(current_state->current_controls & IS_CONNECTION_LAT) &&
            distance > rewiring_data->size_ff_prob)
        || ((current_state->current_controls & IS_CONNECTION_LAT) &&
            distance > rewiring_data->size_lat_prob)) {
        return false;
    }

    if (!(current_state->current_controls & IS_CONNECTION_LAT)) {
        probability = rewiring_data->ff_probabilities[distance];
    } else {
        probability = rewiring_data->lat_probabilities[distance];
    }
    uint16_t r = ulrbits(mars_kiss64_seed(rewiring_data->local_seed)) * MAX_SHORT;
    if (r > probability) {
        return false;
    }
    // else, skip

    return sp_structs_add_synapse(rewiring_data, current_state, row);
}

#endif // _FORMATION_DISTANCE_DEPENDENT_H_
