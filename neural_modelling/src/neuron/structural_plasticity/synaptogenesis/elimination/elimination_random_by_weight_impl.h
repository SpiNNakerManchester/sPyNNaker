/*
 * Copyright (c) 2017 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Synapse elimination by weighted random selection
#ifndef _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_
#define _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_

#include "elimination.h"

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
