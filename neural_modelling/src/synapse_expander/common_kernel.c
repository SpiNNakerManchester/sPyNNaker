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

/**
 *! \file
 *! \brief Common functions for kernel generation
 */
#include "common_kernel.h"
#include <stdlib.h>

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
        *out_row = -d + 1;
    } else {
        d = (int16_t) uidiv((uint16_t) d, step_row, &r);
        *out_row = d + 1;
    }

    d = (int16_t) (in_col - start_col - 1);
    if (d == 0) {
        *out_col = 1;
    } else if (d < 0) {
        d = (int16_t) uidiv((uint16_t) (-d), step_col, &r);
        *out_col = -d + 1;
    } else {
        d = (int16_t) uidiv((uint16_t) d, step_col, &r);
        *out_col = d + 1;
    }
}
