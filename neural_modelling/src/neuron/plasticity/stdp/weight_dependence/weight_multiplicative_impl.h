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
    accum min_weight;    //!< Minimum weight
    accum max_weight;    //!< Maximum weight

    accum a2_plus;       //!< Amount to move weight on potentiation
    accum a2_minus;      //!< Amount to move weight on depression
} plasticity_weight_region_data_t;

//! The current state data for the rule
typedef struct {
    accum weight;        //!< The current weight

    //! The shift to use when multiplying
    uint32_t weight_shift;
    //! Reference to the configuration data
    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "weight_one_term.h"

static inline accum mul(accum a, int32_t stdp_fixed) {
    return kbits((bitsk(a) * stdp_fixed) >> STDP_FIXED_POINT);
}

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
//! \param[in] depression: The amount of depression to apply
//! \return the updated weight state
static inline weight_state_t weight_one_term_apply_depression(
        weight_state_t state, int32_t depression) {
    // Calculate scale
    accum scale = (state.weight - state.weight_region->min_weight) *
            state.weight_region->a2_minus;

    // Multiply scale by depression and subtract
    state.weight -= mul(scale, depression);
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
    state.weight += mul(scale, potentiation);
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

static inline void weight_decay(weight_state_t state, int32_t decay) {
    state.weight = mul(state.weight, decay);
}

static inline int32_t weight_get_update(weight_state_t state) {
    return bitsk(state.weight) >> S1615_TO_STDP_RIGHT_SHIFT;
}

#endif  // _WEIGHT_MULTIPLICATIVE_IMPL_H_
