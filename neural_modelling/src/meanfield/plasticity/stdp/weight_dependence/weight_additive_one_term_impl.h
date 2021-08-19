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
    int32_t min_weight;     //!< Minimum weight
    int32_t max_weight;     //!< Maximum weight

    int32_t a2_plus;        //!< Scaling factor for weight delta on potentiation
    int32_t a2_minus;       //!< Scaling factor for weight delta on depression
} plasticity_weight_region_data_t;

//! The current state data for the rule
typedef struct {
    int32_t initial_weight; //!< The starting weight

    int32_t a2_plus;        //!< Cumulative potentiation delta
    int32_t a2_minus;       //!< Cumulative depression delta

    //! Reference to the configuration data
    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "../../../../meanfield/plasticity/stdp/weight_dependence/weight_one_term.h"

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
    state.a2_minus += a2_minus;
    return state;
}

//---------------------------------------
//! \brief Apply the potentiation rule to the weight state
//! \param[in] state: The weight state to update
//! \param[in] a2_plus: The amount of potentiation to apply
//! \return the updated weight state
static inline weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t a2_plus) {
    state.a2_plus += a2_plus;
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
    // **NOTE** A2+ and A2- are pre-scaled into weight format
    int32_t scaled_a2_plus = STDP_FIXED_MUL_16X16(
            new_state.a2_plus, new_state.weight_region->a2_plus);
    int32_t scaled_a2_minus = STDP_FIXED_MUL_16X16(
            new_state.a2_minus, new_state.weight_region->a2_minus);

    // Apply all terms to initial weight
    int32_t new_weight =
            new_state.initial_weight + scaled_a2_plus - scaled_a2_minus;

    // Clamp new weight
    new_weight = MIN(new_state.weight_region->max_weight,
            MAX(new_weight, new_state.weight_region->min_weight));

    log_debug("\told_weight:%u, a2+:%d, a2-:%d, scaled a2+:%d, scaled a2-:%d,"
            " new_weight:%d",
            new_state.initial_weight, new_state.a2_plus, new_state.a2_minus,
            scaled_a2_plus, scaled_a2_minus, new_weight);

    return (weight_t) new_weight;
}

#endif // _WEIGHT_ADDITIVE_ONE_TERM_IMPL_H_
