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

/*!
 * \dir
 * \brief STDP weight dependence rules
 * \file
 * \brief interface for different weight implementations for the weight half of
 * a STDP rule.
 *
 * \details the API interface contains:
 *  - weight_initialise():
 *        Initialises the weight aspect of a STDP rule.
 *  - weight_get_initial():
 *        Converts the stored weight into an update-able form.
 *  - weight_get_final():
 *        Converts the updated weight into store-able form.
 */

#ifndef _WEIGHT_H_
#define _WEIGHT_H_

#include <common/neuron-typedefs.h>
#include <neuron/synapse_row.h>

/*!
 * \brief Initialises the weight aspect of an STDP rule.
 * \param[in] address: the absolute address in SRAM where the weight parameters
 *      are stored.
 * \param[in] n_synapse_types: The number of synapse types
 * \param[in] min_weights: The value of the weight of the LSB of the weight
 * \return the end of the weight region as an absolute SDRAM memory address.
 */
address_t weight_initialise(
        address_t address, uint32_t n_synapse_types, REAL *min_weights, REAL *min_weights_recip);

/*!
 * \brief Gets the initial weight state.
 * \param[in] weight: The weight at the start
 * \param[in] synapse_type: The type of synapse involved
 * \return The initial weight state.
 */
static weight_state_t weight_get_initial(weight_t weight, index_t synapse_type);

/*!
 * \brief Gets the final weight.
 * \param[in] new_state: The updated weight state
 * \return The new weight.
 */
static weight_t weight_get_final(weight_state_t new_state);

/*!
 * \brief Decay the weight inside the state by multiplication
 * \param[in] state The state containing the current weight
 * \param[in] decay The "decay" to multiply the weight by, in STDP fixed point
 *                  format
 */
static void weight_decay(weight_state_t *state, int32_t decay);

/*!
 * \brief Get the weight inside during update in STDP fixed point format
 * \param[in] state The state containing the current weight
 * \return The weight in s1615 format
 */
static accum weight_get_update(weight_state_t state);

#endif // _WEIGHT_H_
