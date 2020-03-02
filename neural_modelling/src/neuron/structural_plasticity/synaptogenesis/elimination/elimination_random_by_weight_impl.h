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

#ifndef _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_
#define _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_

#include "elimination.h"

struct elimination_params {
    uint32_t prob_elim_depression;
    uint32_t prob_elim_potentiation;
    uint32_t threshold;
};

static inline bool synaptogenesis_elimination_rule(
        current_state_t *current_state, struct elimination_params* params,
        uint32_t time, address_t row) {
    use(time);

    uint32_t r = mars_kiss64_seed(*(current_state->local_seed));

    // Is weight depressed?
    if (current_state->weight < params->threshold && r > params->prob_elim_depression) {
        return false;
    }

    // Is weight potentiated or unchanged?
    if (current_state->weight >= params->threshold && r > params->prob_elim_potentiation) {
        return false;
    }

    return sp_structs_remove_synapse(current_state, row);
}

#endif // _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_
