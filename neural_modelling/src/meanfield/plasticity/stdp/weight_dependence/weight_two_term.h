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
//! \brief API for dual-term weight dependence rules
#ifndef _WEIGHT_TWO_TERM_H_
#define _WEIGHT_TWO_TERM_H_

#include "../../../../meanfield/plasticity/stdp/weight_dependence/weight.h"

//! \brief Apply the depression rule to the weight state
//! \param[in] state: The weight state to update
//! \param[in] depression_1: The amount of depression to apply to term 1
//! \param[in] depression_2: The amount of depression to apply to term 2
//! \return the updated weight state
static weight_state_t weight_two_term_apply_depression(
        weight_state_t state, int32_t depression_1, int32_t depression_2);

//! \brief Apply the potentiation rule to the weight state
//! \param[in] state: The weight state to update
//! \param[in] potentiation_1: The amount of potentiation to apply to term 1
//! \param[in] potentiation_2: The amount of potentiation to apply to term 2
//! \return the updated weight state
static weight_state_t weight_two_term_apply_potentiation(
        weight_state_t state, int32_t potentiation_1, int32_t potentiation_2);

#endif // _WEIGHT_TWO_TERM_H_
