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

#ifndef _THRESHOLD_TYPE_NONE_H_
#define _THRESHOLD_TYPE_NONE_H_

#include "threshold_type.h"

typedef struct threshold_type_t {
} threshold_type_t;

static inline bool threshold_type_is_above_threshold(
        state_t value, threshold_type_pointer_t threshold_type) {
	use(value);
	use(threshold_type);
    return 0;
}

#endif // _THRESHOLD_TYPE_NONE_H_
