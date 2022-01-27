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
 * \brief Fixed-Total-Number (Multapse) Connection generator implementation
 */

#include <log.h>
#include <synapse_expander/rng.h>
#include <synapse_expander/generator_types.h>

//! The parameters that can be copied from SDRAM
struct fixed_total_params {
    uint32_t pre_lo;
    uint32_t pre_hi;
    uint32_t post_lo;
    uint32_t post_hi;
    uint32_t allow_self_connections;
    uint32_t with_replacement;
    uint32_t n_connections;
    uint32_t n_potential_synapses;
};

/**
 * \brief The data to be passed around.
 *
 * This includes the parameters, and the RNG of the connector.
 */
struct fixed_total {
    struct fixed_total_params params;
    rng_t *rng;
};

/**
 * \brief Initialise the fixed-total connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *connection_generator_fixed_total_initialise(void **region) {
    // Allocate memory for the parameters
    struct fixed_total *obj = spin1_malloc(sizeof(struct fixed_total));

    // Copy the parameters in
    struct fixed_total_params *params_sdram = *region;
    obj->params = *params_sdram;
    *region = &params_sdram[1];

    // Initialise the RNG
    obj->rng = rng_init(region);
    log_debug("Fixed Total Number Connector, pre_lo = %u, pre_hi = %u, "
    		"post_lo = %u, post_hi = %u, allow self connections = %u, "
            "with replacement = %u, n connections = %u, "
            "n potential connections = %u",
			obj->params.pre_lo, obj->params.pre_hi,
			obj->params.post_lo, obj->params.post_hi,
            obj->params.allow_self_connections,
            obj->params.with_replacement, obj->params.n_connections,
            obj->params.n_potential_synapses);
    return obj;
}

/**
 * \brief Free the fixed-total connection generator
 * \param[in] generator: The generator to free
 */
static void connection_generator_fixed_total_free(void *generator) {
    struct fixed_total *params = generator;
    rng_free(params->rng);
    sark_free(generator);
}

static inline uint32_t _pick(rng_t *rng, uint32_t K, uint32_t not_K) {
    return (uint32_t) (ulrbits(rng_generator(rng)) * (K + not_K));
}

/**
 * \brief Draw from a binomial distribution i.e. with replacement
 * \param[in] n: The number of times the experiment is run
 * \param[in] N: The number of items in the bag
 * \param[in] K: The number of items that are valid
 * \param[in] rng: The uniform random number generator
 * \return The number of times a valid item was drawn
 */
static uint32_t binomial(uint32_t n, uint32_t N, uint32_t K, rng_t *rng) {
    uint32_t count = 0;
    uint32_t not_K = N - K;
    for (uint32_t i = 0; i < n; i++) {
        if (_pick(rng, K, not_K) < K) {
            count++;
        }
    }
    return count;
}

/**
 * \brief Draw from a hyper-geometric distribution i.e. without replacement
 * \param[in] n: The number of times the experiment is run
 * \param[in] N: The number of items in the bag at the start
 * \param[in] K: The number of valid items in the bag at the start
 * \param[in] rng: The uniform random number generator
 * \return The number of times a valid item was drawn
 */
static uint32_t hypergeom(uint32_t n, uint32_t N, uint32_t K, rng_t *rng) {
    uint32_t count = 0;
    uint32_t K_remaining = K;
    uint32_t not_K_remaining = N - K;
    for (uint32_t i = 0; i < n; i++) {
        if (_pick(rng, K_remaining, not_K_remaining) < K_remaining) {
            count++;
            K_remaining--;
        } else {
            not_K_remaining--;
        }
    }
    return count;
}

/**
 * \brief Generate connections with the fixed-total connection generator
 * \param[in] generator: The generator to use to generate connections
 * \param[in] pre_slice_start: The start of the slice of the pre-population
 *                             being generated
 * \param[in] pre_slice_count: The number of neurons in the slice of the
 *                             pre-population being generated
 * \param[in] pre_neuron_index: The index of the neuron in the pre-population
 *                              being generated
 * \param[in] post_slice_start: The start of the slice of the post-population
 *                              being generated
 * \param[in] post_slice_count: The number of neurons in the slice of the
 *                              post-population being generated
 * \param[in] max_row_length: The maximum number of connections to generate
 * \param[in,out] indices: An array into which the core-relative post-indices
 *                         should be placed.  This will be initialised to be
 *                         \p max_row_length in size
 * \return The number of connections generated
 */
static uint32_t connection_generator_fixed_total_generate(
        void *generator, UNUSED uint32_t pre_slice_start,
        UNUSED uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    // If there are no connections left or none to be made, return 0
    struct fixed_total *obj = generator;
    if (max_row_length == 0 || obj->params.n_connections == 0) {
        return 0;
    }

    // If not in the pre-population view range, then don't generate
    if ((pre_neuron_index < obj->params.pre_lo) ||
    		(pre_neuron_index > obj->params.pre_hi)) {
    	return 0;
    }

    // Work out how many values can be sampled from (on this slice)
    uint32_t slice_lo = post_slice_start;
    uint32_t slice_hi = post_slice_start + post_slice_count - 1;

    // If everything is off the current slice then don't generate
    if ((obj->params.post_hi < slice_lo) ||
    		(obj->params.post_lo > slice_hi)) {
    	return 0;
    }

    // Otherwise work out how many values can be sampled from
    if ((obj->params.post_lo >= post_slice_start) &&
    		(obj->params.post_lo < post_slice_start + post_slice_count)) {
    	slice_lo = obj->params.post_lo;
    	if (obj->params.post_hi >= post_slice_start + post_slice_count) {
    		slice_hi = post_slice_start + post_slice_count - 1;
    	} else {
    		slice_hi = obj->params.post_hi;
    	}
    } else { // post_lo is less than slice_start
    	slice_lo = post_slice_start;
    	if (obj->params.post_hi >= post_slice_start + post_slice_count) {
    		slice_hi = post_slice_start + post_slice_count - 1;
    	}
    	else {
    		slice_hi = obj->params.post_hi;
    	}
    }

    uint32_t n_values = slice_hi - slice_lo + 1;
    if (!obj->params.allow_self_connections
            && pre_neuron_index >= obj->params.post_lo
            && pre_neuron_index <= obj->params.post_hi) {
        n_values--;
    }
    uint32_t n_conns = 0;

    // If we're on the last row of the sub-matrix, then all of the remaining
    // sub-matrix connections get allocated to this row
    if (pre_neuron_index == obj->params.pre_hi) {
        n_conns = obj->params.n_connections;
    } else {
        // If with replacement, generate a binomial for this row
        if (obj->params.with_replacement) {
            n_conns = binomial(
                    obj->params.n_connections,
                    obj->params.n_potential_synapses, n_values, obj->rng);
        // If without replacement, generate a hyper-geometric for this row
        } else {
            n_conns = hypergeom(
                    obj->params.n_connections,
                    obj->params.n_potential_synapses, n_values, obj->rng);
        }
    }

    // If too many connections, limit
    if (n_conns > max_row_length) {
        if (pre_neuron_index == obj->params.pre_hi) {
            log_warning("Could not create %u connections",
                    n_conns - max_row_length);
        }
        n_conns = max_row_length;
    }
    log_debug("Generating %u of %u synapses",
    		n_conns, obj->params.n_connections);

    // Sample from the possible connections in this row n_conns times
    if (obj->params.with_replacement) {
        // Sample them with replacement
        for (unsigned int i = 0; i < n_conns; i++) {
            uint32_t u01 = rng_generator(obj->rng) & 0x00007fff;
            uint32_t j = (u01 * n_values) >> 15;
            indices[i] = j + slice_lo - post_slice_start;
        }
    } else {
        // Sample them without replacement using reservoir sampling
        for (unsigned int i = 0; i < n_conns; i++) {
            indices[i] = i + slice_lo - post_slice_start;
        }
        for (unsigned int i = n_conns; i < n_values; i++) {
            // j = random(0, i) (inclusive)
            const unsigned int u01 = rng_generator(obj->rng) & 0x00007fff;
            const unsigned int j = (u01 * (i + 1)) >> 15;
            if (j < n_conns) {
                indices[j] = i + slice_lo - post_slice_start;
            }
        }
    }

    obj->params.n_connections -= n_conns;
    obj->params.n_potential_synapses -= n_values;

    return n_conns;
}
