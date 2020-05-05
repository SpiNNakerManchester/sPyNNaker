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
 * \file
 * \brief Common functions for kernel generation
 */
#include <common-typedefs.h>

uint16_t uidiv(uint32_t dividend, uint16_t divider, uint16_t *remainder);

/**
 * \brief Get the post's coordinates in the pre's coordinate system
 * \param[in] in_row: post row coordinate
 * \param[in] in_col: post column coordinate
 * \param[in] start_row: row offset
 * \param[in] start_col: column offset
 * \param[in] step_row: row step
 * \param[in] step_col: column step
 * \param[out] out_row: pre row coordinate
 * \param[out] out_col: pre column coordinate
 */
void post_in_pre_world(uint16_t in_row, uint16_t in_col,
        uint16_t start_row, uint16_t start_col,
        uint16_t step_row, uint16_t step_col,
        uint16_t *out_row, uint16_t *out_col);

/**
 * \brief Get the pre's coordinates in the post's coordinate system
 * \param[in] in_row: pre row coordinate
 * \param[in] in_col: pre column coordinate
 * \param[in] start_row: row offset
 * \param[in] start_col: column offset
 * \param[in] step_row: row step
 * \param[in] step_col: column step
 * \param[out] out_row: post row coordinate
 * \param[out] out_col: post column coordinate
 */
void pre_in_post_world(uint16_t in_row, uint16_t in_col, uint16_t start_row,
        uint16_t start_col, uint16_t step_row, uint16_t step_col,
        int16_t *out_row, int16_t *out_col);
