/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _FORMATION_DISTANCE_DEPENDENT_H_
#define _FORMATION_DISTANCE_DEPENDENT_H_

#include "formation.h"

#define MAX_SHORT 65535

struct formation_params {
    uint32_t grid_x;
    uint32_t grid_y;
    uint32_t ff_prob_size;
    uint32_t lat_prob_size;
    uint16_t prob_tables[];
};


//! abs function
static int my_abs(int a) {
    return a < 0 ? -a : a;
}

static inline bool synaptogenesis_formation_rule(
        current_state_t *current_state, struct formation_params *params,
        uint32_t time, address_t row) {
    use(time);

    // Compute distances
    // To do this I need to take the DIV and MOD of the
    // post-synaptic neuron ID, of the pre-synaptic neuron ID
    // Compute the distance of these 2 measures
    int32_t pre_x, pre_y, post_x, post_y, pre_global_id, post_global_id;
    // Pre computation requires querying the table with global information
    pre_global_id = current_state->key_atom_info->lo_atom +
            current_state->pre_syn_id;
    post_global_id = current_state->post_syn_id + current_state->post_low_atom;

    if (params->grid_x > 1) {
        pre_x = pre_global_id / params->grid_x;
        post_x = post_global_id / params->grid_x;
    } else {
        pre_x = 0;
        post_x = 0;
    }

    if (params->grid_y > 1) {
        pre_y = pre_global_id % params->grid_y;
        post_y = post_global_id % params->grid_y;
    } else {
        pre_y = 0;
        post_y = 0;
    }

    // With periodic boundary conditions
    uint delta_x, delta_y;
    delta_x = my_abs(pre_x - post_x);
    delta_y = my_abs(pre_y - post_y);

    if (delta_x > params->grid_x >> 1 && params->grid_x > 1) {
        delta_x -= params->grid_x;
    }

    if (delta_y > params->grid_y >> 1 && params->grid_y > 1) {
        delta_y -= params->grid_y;
    }

    uint32_t distance = delta_x * delta_x + delta_y * delta_y;

    // Distance based probability extracted from the appropriate LUT
    uint16_t probability;
    int16_t controls = current_state->pre_population_info->sp_control;
    if (!(controls & IS_CONNECTION_LAT)) {
        if (distance >= params->ff_prob_size) {
            return false;
        }
        probability = params->prob_tables[distance];
    } else {
        if (distance >= params->lat_prob_size) {
            return false;
        }
        probability = params->prob_tables[params->ff_prob_size + distance];
    }
    uint16_t r = ulrbits(mars_kiss64_seed(*(current_state->local_seed)))
            * MAX_SHORT;
    if (r > probability) {
        return false;
    }

    return sp_structs_add_synapse(current_state, row);
}

#endif // _FORMATION_DISTANCE_DEPENDENT_H_
