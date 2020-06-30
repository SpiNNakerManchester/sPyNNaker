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
    int32_t min_weight;    //!< Minimum weight
    int32_t max_weight;    //!< Maximum weight

    int32_t a2_plus;       //!< Amount to move weight on potentiation
    int32_t a2_minus;      //!< Amount to move weight on depression
} plasticity_weight_region_data_t;

//! The current state data for the rule
typedef struct {
    int32_t weight;        //!< The current weight

    //! The shift to use when multiplying
    uint32_t weight_multiply_right_shift;
    //! Reference to the configuration data
    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "weight_one_term.h"

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
    extern uint32_t *weight_multiply_right_shift;

    return (weight_state_t) {
        .weight = (int32_t) weight,
        .weight_multiply_right_shift =
                weight_multiply_right_shift[synapse_type],
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
    // **NOTE** this calculation must be done at runtime-defined weight
    // fixed-point format
    int32_t scale = maths_fixed_mul16(
            state.weight - state.weight_region->min_weight,
            state.weight_region->a2_minus, state.weight_multiply_right_shift);

    // Multiply scale by depression and subtract
    // **NOTE** using standard STDP fixed-point format handles format conversion
    state.weight -= STDP_FIXED_MUL_16X16(scale, depression);
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
    // **NOTE** this calculation must be done at runtime-defined weight
    // fixed-point format
    int32_t scale = maths_fixed_mul16(
            state.weight_region->max_weight - state.weight,
            state.weight_region->a2_plus, state.weight_multiply_right_shift);

    // Multiply scale by potentiation and add
    // **NOTE** using standard STDP fixed-point format handles format conversion
    state.weight += STDP_FIXED_MUL_16X16(scale, potentiation);
    return state;
}
//---------------------------------------
/*!
 * \brief Gets the final weight.
 * \param[in] new_state: The updated weight state
 * \return The new weight.
 */
static inline weight_t weight_get_final(weight_state_t new_state) {
    log_debug("\tnew_weight:%d\n", new_state.weight);

    return (weight_t) new_state.weight;
}

#endif  // _WEIGHT_MULTIPLICATIVE_IMPL_H_
