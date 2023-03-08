/*
 * Copyright (c) 2017 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * \file
 * \brief Common functions for kernel generation
 */
#include "common_kernel.h"
#include <stdlib.h>

//! \brief Unsigned integer division.
//! \param[in] dividend: The value being divided
//! \param[in] divider: The value doing the dividing
//! \param[out] remainder: The remainder
//! \return The quotient
uint16_t uidiv(uint32_t dividend, uint16_t divider, uint16_t *remainder) {
    if (dividend == 0 || dividend < divider) {
    	*remainder = (uint16_t) dividend;
        return 0;
    }

    // Assumes that the dividend is less than 1<<31
    div_t results = div((int) dividend, (int) (uint32_t) divider);
    *remainder = (uint16_t) results.rem;
    return (uint16_t) results.quot;
}

void post_in_pre_world(uint16_t in_row, uint16_t in_col,
        uint16_t start_row, uint16_t start_col,
        uint16_t step_row, uint16_t step_col,
        uint16_t *out_row, uint16_t *out_col) {
    *out_row = start_row + in_row * step_row;
    *out_col = start_col + in_col * step_col;
}

void pre_in_post_world(uint16_t in_row, uint16_t in_col, uint16_t start_row,
        uint16_t start_col, uint16_t step_row, uint16_t step_col,
        int16_t *out_row, int16_t *out_col) {
    int16_t d = (int16_t) (in_row - start_row - 1);
    uint16_t r;
    if (d == 0) {
        *out_row = 1;
    } else if (d < 0) {
        d = (int16_t) uidiv((uint16_t) (-d), step_row, &r);
        if (r == 0) {
            *out_row = -d + 1;
        } else {
        	*out_row = -d; // Note: e.g. ((-1) // 4) is not the same as (- (1 // 4))
        }
    } else {
        d = (int16_t) uidiv((uint16_t) d, step_row, &r);
        *out_row = d + 1;
    }

    d = (int16_t) (in_col - start_col - 1);
    if (d == 0) {
        *out_col = 1;
    } else if (d < 0) {
        d = (int16_t) uidiv((uint16_t) (-d), step_col, &r);
        if (r == 0) {
        	*out_col = -d + 1;
        } else {
        	*out_col = -d; // Note: e.g. ((-1) // 4) is not the same as (- (1 // 4))
        }
    } else {
        d = (int16_t) uidiv((uint16_t) d, step_col, &r);
        *out_col = d + 1;
    }
}
