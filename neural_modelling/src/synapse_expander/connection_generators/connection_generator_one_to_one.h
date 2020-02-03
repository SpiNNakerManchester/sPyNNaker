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
 *! \brief One-to-One Connection generator implementation
 */

#include <synapse_expander/generator_types.h>

static initialize_func connection_generator_one_to_one_initialise;
static free_func connection_generator_one_to_one_free;
static generate_connection_func connection_generator_one_to_one_generate;

/**
 *! \brief The parameters to be passed around for this connector
 */
struct one_to_one {
    uint32_t pre_lo;
    uint32_t pre_hi;
    uint32_t post_lo;
    uint32_t post_hi;
};

static void *connection_generator_one_to_one_initialise(address_t *region) {
    struct one_to_one *params = spin1_malloc(sizeof(struct one_to_one));
    struct one_to_one *params_sdram = (void *) *region;

    // Copy the parameters into the data structure
    *params = *params_sdram++;
    *region = (void *) params_sdram;

    log_debug("One to one connector, pre_lo = %u, pre_hi = %u, "
            "post_lo = %u, post_hi = %u",
            params->pre_lo, params->pre_hi, params->post_lo, params->post_hi);

    return params;
//    use(region);
//    log_debug("One to One connector");
//    return NULL;
}

static void connection_generator_one_to_one_free(void *data) {
    sark_free(data);
}

static uint32_t connection_generator_one_to_one_generate(
        void *data,  uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(post_slice_count);
    use(pre_slice_start);
    use(pre_slice_count);

    struct one_to_one *obj = data;
    log_debug("pre_neuron_index %u", pre_neuron_index);

    // If no space, generate nothing
    if (max_row_length < 1) {
        return 0;
    }

    // If not in the pre-population view range, then don't generate
    if ((pre_neuron_index < obj->pre_lo) ||
            (pre_neuron_index > obj->pre_hi)) {
        return 0;
    }

    // Post-index = view-relative pre-index
    // Note that this could be negative (but see later)
    int post_neuron_index = pre_neuron_index - obj->pre_lo + obj->post_lo;

    // If not in the post-population view range, then don't generate.
    // This will filter negatives
    if ((post_neuron_index < (int) obj->post_lo) ||
            (post_neuron_index > (int) obj->post_hi)) {
        return 0;
    }

    // If out of range, don't generate anything
    if ((post_neuron_index < (int) post_slice_start) ||
            (post_neuron_index >= (int) (post_slice_start + post_slice_count))) {
        return 0;
    }

    // Post-index = core-relative post-index
    indices[0] = post_neuron_index - post_slice_start;
    return 1;
}
