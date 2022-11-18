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
//! \brief Additive dual-term weight dependence rule
#ifndef _WEIGHT_ADDITIVE_TWO_TERM_IMPL_H_
#define _WEIGHT_ADDITIVE_TWO_TERM_IMPL_H_

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>
#include <neuron/synapse_row.h>

//#include <debug.h>

//---------------------------------------
// Structures
//---------------------------------------
//! The configuration of the rule
typedef struct plasticity_weight_region_data_two_term_t {
    accum min_weight;     //!< Minimum weight
    accum max_weight;     //!< Maximum weight

    accum a2_plus;        //!< Scaling factor for weight delta on potentiation
    accum a2_minus;       //!< Scaling factor for weight delta on depression
    accum a3_plus;        //!< Scaling factor for weight delta on potentiation
    accum a3_minus;       //!< Scaling factor for weight delta on depression
} plasticity_weight_region_data_t;

//! The current state data for the rule
typedef struct weight_state_t {
    accum weight;         //!< The weight
    uint32_t weight_shift;  //!< Shift of weight to and from S1615 format

    //! Reference to the configuration data
    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "weight_two_term.h"

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
//! \param[in] a2_minus: The amount of depression to apply to term 1
//! \param[in] a3_minus: The amount of depression to apply to term 2
//! \return the updated weight state
static inline weight_state_t weight_two_term_apply_depression(
        weight_state_t state, int32_t a2_minus, int32_t a3_minus) {
    state.weight -= mul_accum_fixed(state.weight_region->a2_minus, a2_minus);
    state.weight -= mul_accum_fixed(state.weight_region->a3_minus, a3_minus);
    state.weight = kbits(MAX(bitsk(state.weight), bitsk(state.weight_region->min_weight)));
    return state;
}

//---------------------------------------
//! \brief Apply the potentiation rule to the weight state
//! \param[in] state: The weight state to update
//! \param[in] a2_plus: The amount of potentiation to apply to term 1
//! \param[in] a3_plus: The amount of potentiation to apply to term 2
//! \return the updated weight state
static inline weight_state_t weight_two_term_apply_potentiation(
        weight_state_t state, int32_t a2_plus, int32_t a3_plus) {
    state.weight += mul_accum_fixed(state.weight_region->a2_plus, a2_plus);
    state.weight += mul_accum_fixed(state.weight_region->a3_plus, a3_plus);
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

#endif  // _WEIGHT_ADDITIVE_TWO_TERM_IMPL_H_
