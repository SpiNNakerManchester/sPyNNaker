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

#include <debug.h>

//---------------------------------------
// Structures
//---------------------------------------
//! The configuration of the rule
typedef struct plasticity_weight_region_data_two_term_t {
    int32_t min_weight;     //!< Minimum weight
    int32_t max_weight;     //!< Maximum weight

    int32_t a2_plus;        //!< Scaling factor for weight delta on potentiation
    int32_t a2_minus;       //!< Scaling factor for weight delta on depression
    int32_t a3_plus;        //!< Scaling factor for weight delta on potentiation
    int32_t a3_minus;       //!< Scaling factor for weight delta on depression
} plasticity_weight_region_data_t;

//! The current state data for the rule
typedef struct weight_state_t {
    int32_t initial_weight; //!< The starting weight

    int32_t a2_plus;        //!< Cumulative potentiation delta (term 1)
    int32_t a2_minus;       //!< Cumulative depression delta (term 1)
    int32_t a3_plus;        //!< Cumulative potentiation delta (term 2)
    int32_t a3_minus;       //!< Cumulative depression delta (term 2)

    //! Reference to the configuration data
    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "../../../../meanfield/plasticity/stdp/weight_dependence/weight_two_term.h"

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

    return (weight_state_t) {
        .initial_weight = (int32_t) weight,
        .a2_plus = 0,
        .a2_minus = 0,
        .a3_plus = 0,
        .a3_minus = 0,
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
    state.a2_minus += a2_minus;
    state.a3_minus += a3_minus;
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
    state.a2_plus += a2_plus;
    state.a3_plus += a3_plus;
    return state;
}

//---------------------------------------
/*!
 * \brief Gets the final weight.
 * \param[in] new_state: The updated weight state
 * \return The new weight.
 */
static inline weight_t weight_get_final(weight_state_t new_state) {
    // Scale potentiation and depression
    // **NOTE** A2+, A2-, A3+ and A3- are pre-scaled into weight format
    int32_t scaled_a2_plus = STDP_FIXED_MUL_16X16(
            new_state.a2_plus, new_state.weight_region->a2_plus);
    int32_t scaled_a2_minus = STDP_FIXED_MUL_16X16(
            new_state.a2_minus, new_state.weight_region->a2_minus);
    int32_t scaled_a3_plus = STDP_FIXED_MUL_16X16(
            new_state.a3_plus, new_state.weight_region->a3_plus);
    int32_t scaled_a3_minus = STDP_FIXED_MUL_16X16(
            new_state.a3_minus, new_state.weight_region->a3_minus);

    // Apply all terms to initial weight
    int32_t new_weight = new_state.initial_weight + scaled_a2_plus
            + scaled_a3_plus - scaled_a2_minus - scaled_a3_minus;

    // Clamp new weight
    new_weight = MIN(new_state.weight_region->max_weight,
            MAX(new_weight, new_state.weight_region->min_weight));

    log_debug("\told_weight:%u, a2+:%d, a2-:%d, a3+:%d, a3-:%d",
            new_state.initial_weight, new_state.a2_plus,
            new_state.a2_minus, new_state.a3_plus, new_state.a3_minus);
    log_debug("\tscaled a2+:%d, scaled a2-:%d, scaled a3+:%d, scaled a3-:%d,"
            " new_weight:%d",
            scaled_a2_plus, scaled_a2_minus, scaled_a3_plus,
            scaled_a3_minus, new_weight);

    return (weight_t) new_weight;
}

#endif  // _WEIGHT_ADDITIVE_TWO_TERM_IMPL_H_
