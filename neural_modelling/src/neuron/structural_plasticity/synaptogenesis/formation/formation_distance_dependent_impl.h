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

//! \file
//! \brief Synapse formation using a distance-dependent rule
#ifndef _FORMATION_DISTANCE_DEPENDENT_H_
#define _FORMATION_DISTANCE_DEPENDENT_H_

#include "formation.h"

//! Largest value in a `uint16_t`
#define MAX_SHORT 65535

//! \brief Configuration of synapse formation rule
//!
//! Describes the size of grid containing the neurons (the total number of
//! neurons probably ought to be equal to or just a bit under \a grid_x &times;
//! \a grid_y), and two tables of distance-dependent connection probabilities.
//! The FF table describes ??? connection probabilities, and the LAT table
//! describes lateral connection probabilities. Both are keyed by the _square_
//! of the inter-neuron distance.
//!
//! Note that both pre- and post-neurons are assumed to be on the same size of
//! grid, and the inter-layer distance is assumed to be constant (so it can be
//! accounted for in the construction of the tables).
struct formation_params {
    //! Size of grid containing neurons, X-dimension
    uint32_t grid_x;
    //! Size of grid containing neurons, Y-dimension
    uint32_t grid_y;
    //! Reciprocal of grid_x
    unsigned long fract grid_x_recip;
    //! Reciprocal of grid_y
    unsigned long fract grid_y_recip;
    //! Size of FF probability table
    uint32_t ff_prob_size;
    //! Size of LAT probability table
    uint32_t lat_prob_size;
    //! Concatenated probability tables; first the FF table, then the LAT table
    uint16_t prob_tables[];
};

//! \brief abs function
//! \param[in] a: value (must not be `INT_MIN`)
//! \return Absolute value of \a a
static int my_abs(int a) {
    return a < 0 ? -a : a;
}

//! \brief Formation rule for synaptogenesis; picks what neuron in the
//!     _current_ population will have a synapse added, and then performs the
//!     addition.
//! \param[in] current_state: Pointer to current state
//! \param[in] params: Pointer to rewiring data
//! \param[in] time: Time of formation
//! \param[in] row: The row to form within
//! \return if row was modified
static inline bool synaptogenesis_formation_rule(
        current_state_t *current_state, const formation_params_t *params,
        UNUSED uint32_t time, synaptic_row_t row) {
    // Compute distances
    // To do this I need to take the DIV and MOD of the
    // post-synaptic neuron ID, of the pre-synaptic neuron ID
    // Compute the distance of these 2 measures
    uint32_t pre_x, pre_y, post_x, post_y;
    // Pre computation requires querying the table with global information
    uint32_t pre_global_id = current_state->key_atom_info->lo_atom +
            current_state->pre_syn_id;
    uint32_t post_global_id = current_state->post_syn_id +
            current_state->post_low_atom;

    if (params->grid_x > 1) {
        pre_x = muliulr(pre_global_id, params->grid_x_recip);
        post_x = muliulr(post_global_id, params->grid_x_recip);
    } else {
        pre_x = 0;
        post_x = 0;
    }

    if (params->grid_y > 1) {
        uint32_t pre_y_div = muliulr(pre_global_id, params->grid_y_recip);
        uint32_t post_y_div = muliulr(post_global_id, params->grid_y_recip);
        pre_y = pre_global_id - (pre_y_div * params->grid_y);
        post_y = post_global_id - (post_y_div * params->grid_y);
    } else {
        pre_y = 0;
        post_y = 0;
    }

    // With periodic boundary conditions
    uint32_t delta_x, delta_y;
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
    uint32_t r = rand_int(MAX_SHORT, *(current_state->local_seed));
    if (r > probability) {
        return false;
    }

    return sp_structs_add_synapse(current_state, row);
}

#endif // _FORMATION_DISTANCE_DEPENDENT_H_
