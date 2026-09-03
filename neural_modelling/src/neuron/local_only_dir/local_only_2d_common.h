/*
 * Copyright (c) 2023 The University of Manchester
 * based on work Copyright (c) The University of Sussex,
 * Garibaldi Pineda Garcia, James Turner, James Knight and Thomas Nowotny
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

//! A weight value
typedef int16_t lc_weight_t;

//! Dimensions are needed to be signed due to mapping from pre- to post-synaptic.
typedef int16_t lc_dim_t;

//! A coordinate in terms of rows and columns (y and x)
typedef struct {
    lc_dim_t row;
    lc_dim_t col;
} lc_coord_t;

//! A shape in terms of height and width
typedef struct {
    lc_dim_t height;
    lc_dim_t width;
} lc_shape_t;

//! Structure for constants for precise constant integer division (see div_by_const)
typedef struct {
	uint32_t m: 16;
	uint32_t sh1: 8;
	uint32_t sh2: 8;
} div_const;

typedef struct {
	//! The key to match against the incoming message
	uint32_t key;
	//! The mask to select the relevant bits of \p key for matching
	uint32_t mask;
	//! The index into ::connectors for this entry
	uint32_t start: 13;
	//! The number of bits of key used for colour (0 if no colour)
	uint32_t n_colour_bits: 3;
	//! The number of entries in ::connectors for this entry
	uint32_t count: 16;
	//! The mask to apply to the key once shifted to get the core index
	uint32_t core_mask: 16;
	//! The shift to apply to the key to get the core part
	uint32_t mask_shift: 16;
} key_info;

//! \brief Divide by a constant - based on https://doi.org/10.1145/178243.178249
static inline uint32_t div_by_const(uint32_t i, div_const d) {
	uint32_t t1 = (i * d.m) >> 16;
	uint32_t isubt1 = (i - t1) >> d.sh1;
	return (t1 + isubt1) >> d.sh2;
}

static inline uint32_t get_core_id(uint32_t spike, key_info k_info) {
	return ((spike >> k_info.mask_shift) & k_info.core_mask);
}

static inline uint32_t get_local_id(uint32_t spike, key_info k_info) {
	uint32_t local_mask = ~(k_info.mask | (k_info.core_mask << k_info.mask_shift));
    uint32_t local = spike & local_mask;
    return local >> k_info.n_colour_bits;
}
