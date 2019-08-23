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

#ifndef _WEIGHT_ONE_TERM_H_
#define _WEIGHT_ONE_TERM_H_

#include "weight.h"

static weight_state_t weight_one_term_apply_depression(
        weight_state_t state, int32_t depression);

static weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t potentiation);

#endif // _WEIGHT_ONE_TERM_H_
