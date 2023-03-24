/*
 * Copyright (c) 2015 The University of Manchester
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
//! \brief Additive single-term weight dependence rule
#ifndef _WEIGHT_ADDITIVE_ONE_TERM_IMPL_H_
#define _WEIGHT_ADDITIVE_ONE_TERM_IMPL_H_

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>
#include <neuron/synapse_row.h>

#include <debug.h>

//---------------------------------------
// Structures
//---------------------------------------
//! The configuration of the rule
typedef struct {
    accum min_weight;     //!< Minimum weight
    accum max_weight;     //!< Maximum weight

    accum a2_plus;        //!< Scaling factor for weight delta on potentiation
    accum a2_minus;       //!< Scaling factor for weight delta on depression
} plasticity_weight_region_data_t;

//! The current state data for the rule
typedef struct {
    accum weight; //!< The starting weight

    uint32_t weight_shift; //!< Weight shift to S1615 version

    //! Reference to the configuration data
    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "weight_one_term.h"

//---------------------------------------
// STDP weight dependence functions
//---------------------------------------
/*!
 * \brief Gets the initial weight state.
 * \param[in] weight: The weight at the start
 * \param[in] synapse_type: The type of synapse involved
 * \return The initial weight state.
 */
static inline weight_state_t weight_get_initial(
        weight_t weight, index_t synapse_type) {
    extern plasticity_weight_region_data_t *plasticity_weight_region_data;
    extern uint32_t *weight_shift;

    accum s1615_weight = kbits(weight << weight_shift[synapse_type]);
    return (weight_state_t) {
        .weight = s1615_weight,
        .weight_shift = weight_shift[synapse_type],
        .weight_region = &plasticity_weight_region_data[synapse_type]
    };
}

//---------------------------------------
//! \brief Apply the depression rule to the weight state
//! \param[in] state: The weight state to update
//! \param[in] a2_minus: The amount of depression to apply
//! \return the updated weight state
static inline weight_state_t weight_one_term_apply_depression(
        weight_state_t state, int32_t a2_minus) {
    state.weight -= mul_accum_fixed(state.weight_region->a2_minus, a2_minus);
    state.weight = kbits(MAX(bitsk(state.weight), bitsk(state.weight_region->min_weight)));
    return state;
}

//---------------------------------------
//! \brief Apply the potentiation rule to the weight state
//! \param[in] state: The weight state to update
//! \param[in] a2_plus: The amount of potentiation to apply
//! \return the updated weight state
static inline weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t a2_plus) {
    state.weight += mul_accum_fixed(state.weight_region->a2_plus, a2_plus);
    state.weight = kbits(MIN(bitsk(state.weight), bitsk(state.weight_region->max_weight)));
    return state;
}

//---------------------------------------
/*!
 * \brief Gets the final weight.
 * \param[in] state: The updated weight state
 * \return The new weight.
 */
static inline weight_t weight_get_final(weight_state_t state) {
    return (weight_t) (bitsk(state.weight) >> state.weight_shift);
}

static inline void weight_decay(weight_state_t *state, int32_t decay) {
    state->weight = mul_accum_fixed(state->weight, decay);
}

static inline accum weight_get_update(weight_state_t state) {
    return state.weight;
}

#endif // _WEIGHT_ADDITIVE_ONE_TERM_IMPL_H_
