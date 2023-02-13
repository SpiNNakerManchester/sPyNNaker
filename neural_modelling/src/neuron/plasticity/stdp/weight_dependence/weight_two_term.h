/*
 * Copyright (c) 2015-2023 The University of Manchester
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
//! \brief API for dual-term weight dependence rules
#ifndef _WEIGHT_TWO_TERM_H_
#define _WEIGHT_TWO_TERM_H_

#include "weight.h"

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
