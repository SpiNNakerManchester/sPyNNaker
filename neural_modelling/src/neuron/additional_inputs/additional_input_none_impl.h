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

#ifndef _ADDITIONAL_INPUT_TYPE_NONE_H_
#define _ADDITIONAL_INPUT_TYPE_NONE_H_

#include "additional_input.h"

typedef struct additional_input_t {
} additional_input_t;

static input_t additional_input_get_input_value_as_current(
        additional_input_pointer_t additional_input,
        state_t membrane_voltage) {
    use(additional_input);
    use(membrane_voltage);
    return 0;
}

static void additional_input_has_spiked(
        additional_input_pointer_t additional_input) {
    use(additional_input);
}

#endif // _ADDITIONAL_INPUT_TYPE_NONE_H_
