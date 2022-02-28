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
 * \dir
 * \brief Implementation of the synapse expander and delay expander
 * \file
 * \brief The synapse expander for neuron cores
 */

#include <common-typedefs.h>

typedef enum type {
    S1615,
    UINT32,
    INT32,
    U032
} type;

typedef void (*type_writer_func_t)(void *, accum);

typedef struct type_info {
    type type_id;
    uint32_t size;
    type_writer_func_t writer;
} type_info;

static void write_s1615(void *address, accum value) {
    accum *values = (accum *) address;
    values[0] = value;
}

static void write_uint32(void *address, accum value) {
    uint32_t *values = (uint32_t *) address;
    values[0] = (uint32_t) value;
}

static void write_int32(void *address, accum value) {
    int32_t *values = (int32_t *) address;
    values[0] = (int32_t) value;
}

static void write_u032(void *address, accum value) {
    unsigned long fract *values = (unsigned long fract *) address;
    values[0] = (unsigned long fract) value;
}

static type_info type_writers[] = {
    {S1615, sizeof(accum), write_s1615},
    {UINT32, sizeof(uint32_t), write_uint32},
    {INT32, sizeof(int32_t), write_int32},
    {U032, sizeof(unsigned long fract), write_u032}
};

static type_info *get_type_writer(type t) {
    return &type_writers[t];
}
