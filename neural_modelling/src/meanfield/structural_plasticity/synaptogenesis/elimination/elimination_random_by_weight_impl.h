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
//! \brief Synapse elimination by weighted random selection
#ifndef _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_
#define _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_

#include "../../../../meanfield/structural_plasticity/synaptogenesis/elimination/elimination.h"

//! Configuration of synapse elimination rule
struct elimination_params {
    //! Probability of elimination of depressed synapse
    uint32_t prob_elim_depression;
    //! Probability of elimination of potentiated synapse
    uint32_t prob_elim_potentiation;
    //! Threshold below which a synapse is depressed, and above which it is
    //! potentiated
    uint32_t threshold;
};

//! \brief Elimination rule for synaptogenesis
//! \param[in,out] current_state: Pointer to current state
//! \param[in] params: The elimination rule configuration.
//! \param[in] time: Time of elimination
//! \param[in,out] row: The row to eliminate from
//! \return if row was modified
static inline bool synaptogenesis_elimination_rule(
        current_state_t *restrict current_state,
        const elimination_params_t *params,
        UNUSED uint32_t time, synaptic_row_t restrict row) {
    uint32_t random_number = mars_kiss64_seed(*(current_state->local_seed));

    // Is weight depressed?
    if (current_state->weight < params->threshold &&
            random_number > params->prob_elim_depression) {
        return false;
    }

    // Is weight potentiated or unchanged?
    if (current_state->weight >= params->threshold &&
            random_number > params->prob_elim_potentiation) {
        return false;
    }

    return sp_structs_remove_synapse(current_state, row);
}

#endif // _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_
