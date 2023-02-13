/*
 * Copyright (c) 2017-2023 The University of Manchester
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
