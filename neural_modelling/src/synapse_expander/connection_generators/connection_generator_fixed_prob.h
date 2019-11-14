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
 *! \brief Fixed-Probability Connection generator implementation
 */

#include <synapse_expander/rng.h>
#include <synapse_expander/generator_types.h>

static initialize_func connection_generator_fixed_prob_initialise;
static free_func connection_generator_fixed_prob_free;
static generate_connection_func connection_generator_fixed_prob_generate;

/**
 *! \brief The parameters that can be copied in from SDRAM
 */
struct fixed_prob_params {
    uint32_t pre_lo;
    uint32_t pre_hi;
    uint32_t post_lo;
    uint32_t post_hi;
    uint32_t allow_self_connections;
    unsigned long fract probability;
};

/**
 *! \brief The data structure to be passed around for this connector.  This
 *!        includes the parameters and an RNG.
 */
struct fixed_prob {
    struct fixed_prob_params params;
    rng_t rng;
};

static void *connection_generator_fixed_prob_initialise(address_t *region) {
    // Allocate memory for the data
    struct fixed_prob *obj = spin1_malloc(sizeof(struct fixed_prob));

    // Copy the parameters in
    struct fixed_prob_params *params_sdram = (void *) *region;
    obj->params = *params_sdram++;
    *region = (void *) params_sdram;

    // Initialise the RNG for the connector
    obj->rng = rng_init(region);
    log_debug("Fixed Probability Connector, pre_lo = %u, pre_hi = %u, "
    		"post_lo = %u, post_hi = %u, allow self connections = %u, "
            "probability = %k",
			obj->params.pre_lo, obj->params.pre_hi, obj->params.post_lo, obj->params.post_hi,
            obj->params.allow_self_connections,
            (accum) obj->params.probability);
    return obj;
}

static void connection_generator_fixed_prob_free(void *data) {
    struct fixed_prob *params = data;
    rng_free(params->rng);
    sark_free(data);
}

static uint32_t connection_generator_fixed_prob_generate(
        void *data, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(pre_slice_start);
    use(pre_slice_count);

    struct fixed_prob *obj = data;

    // If no space, generate nothing
    if (max_row_length < 1) {
        return 0;
    }

    // If not in the pre-population view range, then don't generate
    if ((pre_neuron_index < obj->params.pre_lo) ||
    		(pre_neuron_index > obj->params.pre_hi)) {
    	return 0;
    }

    // Randomly select connections to each post-neuron
    uint32_t n_conns = 0;
    for (uint32_t i = 0; i < post_slice_count; i++) {
        // Disallow self connections if configured
        if (!obj->params.allow_self_connections &&
                (pre_neuron_index == post_slice_start + i)) {
            continue;
        }

        // Don't generate if the value is not in the range of the post-population view
        if ((i + post_slice_start < obj->params.post_lo) ||
        	(i + post_slice_start > obj->params.post_hi)) {
        	continue;
        }

        // Generate a random number
        unsigned long fract value = ulrbits(rng_generator(obj->rng));

        // If less than our probability, generate a connection if possible
        if ((value <= obj->params.probability) &&
                (n_conns < max_row_length)) {
            indices[n_conns++] = i;
        } else if (n_conns >= max_row_length) {
            log_warning("Row overflow");
        }
    }

    return n_conns;
}
