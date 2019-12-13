/*
 * Copyright (c) 2019 The University of Manchester
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

#ifndef INCLUDED_COMMON_MEM_H
#define INCLUDED_COMMON_MEM_H

#include <common-typedefs.h>

/**
 *! \brief A small and fast version of memcpy; pointers must be aligned and a
 *! whole number of words must be being copied.
 */
static inline void fast_memcpy(
        void *restrict to, const void *restrict from, uint32_t num_bytes) {
    uint32_t *to_ptr = to;
    const uint32_t *from_ptr = from;
    while (num_bytes) {
        *to_ptr++ = *from_ptr++;
        num_bytes -= sizeof(uint32_t);
    }
}

#endif // INCLUDED_COMMON_MEM_H
