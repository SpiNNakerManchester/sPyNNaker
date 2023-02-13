/*
 * Copyright (c) 2020-2023 The University of Manchester
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
 * \brief The type converters for parameter generation
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
