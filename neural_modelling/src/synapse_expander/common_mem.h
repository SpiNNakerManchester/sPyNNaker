/*
 * Copyright (c) 2019 The University of Manchester
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

#ifndef INCLUDED_COMMON_MEM_H
#define INCLUDED_COMMON_MEM_H

#include <common-typedefs.h>

//! \file
//! \brief Utility functions for working with memory.

/**
 * \brief A small and fast version of `memcpy()`.
 * \details Both pointers must be aligned and a whole number of words must be
 *      being copied. The areas of memory must not overlap.
 * \param[out] to: Where to copy to. Must be word-aligned.
 * \param[in] from: Where to copy from. Must be word-aligned.
 * \param[in] num_bytes: The number of bytes to copy. Must be a multiple of 4.
 */
static inline void fast_memcpy(
        void *restrict to, const void *restrict from, size_t num_bytes) {
    uint32_t *to_ptr = to;
    const uint32_t *from_ptr = from;
    while (num_bytes) {
        *to_ptr++ = *from_ptr++;
        num_bytes -= sizeof(uint32_t);
    }
}

#endif // INCLUDED_COMMON_MEM_H
