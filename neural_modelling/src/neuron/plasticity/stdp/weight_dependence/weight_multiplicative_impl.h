/*
 * Copyright (c) 2015 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Multiplicative single-term weight dependence rule
#ifndef _WEIGHT_MULTIPLICATIVE_IMPL_H_
#define _WEIGHT_MULTIPLICATIVE_IMPL_H_

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
    accum min_weight;    //!< Minimum weight
    accum max_weight;    //!< Maximum weight

    accum a2_plus;       //!< Amount to move weight on potentiation
    accum a2_minus;      //!< Amount to move weight on depression
} plasticity_weight_region_data_t;

//! The current state data for the rule
typedef struct {
    accum weight;        //!< The current weight

    REAL min_weight;         //!< The min weight
    REAL min_weight_recip;         //!< The min weight

    //! Reference to the configuration data
    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "weight_one_term.h"

//---------------------------------------
// Externals
//---------------------------------------
extern plasticity_weight_region_data_t *plasticity_weight_region_data;

//---------------------------------------

// Weight dependance functions
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
    extern REAL *min_weight;
    extern REAL *min_weight_recip;

    uint64_t mw = (uint64_t) bitsk(min_weight[synapse_type]);
    uint64_t w = (uint64_t) (weight);

    accum s1615_weight = kbits((int_k_t) mw * w);

    return (weight_state_t) {
        .weight = s1615_weight,
        .min_weight = min_weight[synapse_type],
		.min_weight_recip = min_weight_recip[synapse_type],
        .weight_region = &plasticity_weight_region_data[synapse_type]
    };
}

//---------------------------------------
//! \brief Apply the depression rule to the weight state
//! \param[in] state: The weight state to update
//! \param[in] depression: The amount of depression to apply
//! \return the updated weight state
static inline weight_state_t weight_one_term_apply_depression(
        weight_state_t state, int32_t depression) {
    // Calculate scale
    accum scale = (state.weight - state.weight_region->min_weight) *
            state.weight_region->a2_minus;

    // Multiply scale by depression and subtract
    // **NOTE** using standard STDP fixed-point format handles format conversion
    state.weight -= mul_accum_fixed(scale, depression);

    return state;
}
//---------------------------------------
//! \brief Apply the potentiation rule to the weight state
//! \param[in] state: The weight state to update
//! \param[in] potentiation: The amount of potentiation to apply
//! \return the updated weight state
static inline weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t potentiation) {
    // Calculate scale
    accum scale = (state.weight_region->max_weight - state.weight) *
            state.weight_region->a2_plus;

    // Multiply scale by potentiation and add
    // **NOTE** using standard STDP fixed-point format handles format conversion
    state.weight += mul_accum_fixed(scale, potentiation);

    return state;
}
//---------------------------------------
/*!
 * \brief Gets the final weight.
 * \param[in] state: The updated weight state
 * \return The new weight.
 */
static inline weight_t weight_get_final(weight_state_t state) {
    return (weight_t) (state.weight * state.min_weight_recip);
}

static inline void weight_decay(weight_state_t *state, int32_t decay) {
    state->weight = mul_accum_fixed(state->weight, decay);
}

static inline accum weight_get_update(weight_state_t state) {
    return state.weight;
}

#endif  // _WEIGHT_MULTIPLICATIVE_IMPL_H_
