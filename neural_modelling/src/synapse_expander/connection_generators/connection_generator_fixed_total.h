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
 * \brief Fixed-Total-Number (Multapse) Connection generator implementation
 */

#include <log.h>
#include <synapse_expander/rng.h>
#include <synapse_expander/generator_types.h>

//! The parameters that can be copied from SDRAM
struct fixed_total_params {
    // Whether to connect to self or not
    uint32_t allow_self_connections;
    // Whether to repeat connections or not
    uint32_t with_replacement;
    // The number of synapses to generate in total over all cores
    uint32_t n_synapses_total;
};

/**
 * \brief The data to be passed around.
 *
 * This includes the parameters, and the RNG of the connector.
 */
struct fixed_total {
    struct fixed_total_params params;

    // This is how many connections there are to make per core
    uint16_t *n_connections_per_core;
};

/*static inline uint32_t _pick(rng_t *rng, uint32_t K, uint32_t not_K) {
    return (uint32_t) (ulrbits(rng_generator(rng)) * (K + not_K));
}*/

/**
 * \brief Draw from a binomial distribution i.e. with replacement
 * \param[in] n: The number of times the experiment is run
 * \param[in] N: The number of items in the bag
 * \param[in] K: The number of items that are valid
 * \param[in] rng: The uniform random number generator
 * \return The number of times a valid item was drawn
 */
/*static uint32_t binomial(uint32_t n, uint32_t N, uint32_t K, rng_t *rng) {
    uint32_t count = 0;
    uint32_t not_K = N - K;
    for (uint32_t i = 0; i < n; i++) {
        if (_pick(rng, K, not_K) < K) {
            count++;
        }
    }
    return count;
}*/

/**
 * \brief Draw from a hyper-geometric distribution i.e. without replacement
 * \param[in] n: The number of times the experiment is run
 * \param[in] N: The number of items in the bag at the start
 * \param[in] K: The number of valid items in the bag at the start
 * \param[in] rng: The uniform random number generator
 * \return The number of times a valid item was drawn
 */
/*static uint32_t hypergeom(uint32_t n, uint32_t N, uint32_t K, rng_t *rng) {
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
} */

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

    log_debug("Fixed Total Number Connector, allow self connections = %u, "
            "with replacement = %u, n_synapses_total = %u",
            obj->params.allow_self_connections,
            obj->params.with_replacement, obj->params.n_synapses_total);

    // Go through every core and use the population-level RNG to generate
    // the number of synapses on every core with a binomial.
    /*obj->n_connections_per_core = spin1_malloc(obj->params.n_cores * sizeof(uint16_t));
    uint32_t n_to_go = obj->params.n_synapses_total;
    uint32_t synapses_to_go = obj->params.max_synapses_total;
    for (uint32_t i = 0; i < obj->params.n_cores; i++) {
        if (i + 1 == obj->params.n_cores) {
            // Last core gets the treat
            obj->n_connections_per_core[i] = n_to_go;
        } else {
            // Do a binomial for this core
            uint32_t n_conns = binomial(n_to_go, synapses_to_go,
                    obj->params.max_synapses_per_core, population_rng);
            obj->n_connections_per_core[i] = n_conns;
            n_to_go -= n_conns;
            synapses_to_go -= obj->params.max_synapses_per_core;
        }
    } */

    return obj;
}

/**
 * \brief Free the fixed-total connection generator
 * \param[in] generator: The generator to free
 */
static void connection_generator_fixed_total_free(void *generator) {
    sark_free(generator);
}

static uint32_t random_in_range(rng_t *rng, uint32_t range) {
    unsigned long fract u01 = ulrbits(rng_generator(rng));
    return muliulr(range, u01);
}

static void fixed_total_next(uint32_t *pre, uint32_t *post, uint32_t pre_lo, uint32_t pre_hi) {
    *pre += 1;
    if (*pre > pre_hi) {
        *pre = pre_lo;
        *post += 1;
    }
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
static bool connection_generator_fixed_total_generate(
        void *generator, uint32_t pre_lo, uint32_t pre_hi,
        uint32_t post_lo, uint32_t post_hi, UNUSED uint32_t post_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        unsigned long accum weight_scale, accum timestep_per_delay,
        param_generator_t weight_generator, param_generator_t delay_generator,
        matrix_generator_t matrix_generator) {
    struct fixed_total *obj = generator;

    uint32_t n_pre = pre_hi - pre_lo + 1;
    uint32_t n_post = post_hi - post_lo + 1;
    uint32_t post_slice_end = post_slice_start + post_slice_count;
    uint32_t n_conns = obj->params.n_synapses_total;

    // Generate the connections for all cores then filter for this one
    if (obj->params.with_replacement) {
        for (uint32_t i = 0; i < n_conns; i++) {
            uint32_t post = random_in_range(population_rng, n_post) + post_lo;
            if (post >= post_slice_start && post < post_slice_end) {
                uint32_t local_post = post - post_slice_start;
                accum weight = param_generator_generate(weight_generator);
                uint16_t delay = rescale_delay(
                        param_generator_generate(delay_generator), timestep_per_delay);

                uint32_t pre;
                bool written = false;
                uint32_t n_retries = 0;
                do {
                    pre = random_in_range(core_rng, n_pre) + pre_lo;
                    if (obj->params.allow_self_connections || pre != post) {
                        written = matrix_generator_write_synapse(matrix_generator,
                            pre, local_post, weight, delay, weight_scale);
                        n_retries++;
                    }
                } while (!written && n_retries < 10);
                if (!written) {
                    log_error("Couldn't find a row to write to!");
                    return false;
                }
            }
        }
    } else {
        uint32_t pre = pre_lo;
        uint32_t post = post_lo;
        uint32_t i = 0;
        struct {
            uint32_t pre;
            uint32_t post;
        } conns[n_conns];
        for (i = 0; i < n_conns; i++) {
            conns[i].pre = pre;
            conns[i].post = post;
            fixed_total_next(&pre, &post, pre_lo, pre_hi);
            if (!obj->params.allow_self_connections && (pre == post)) {
                fixed_total_next(&pre, &post, pre_lo, pre_hi);
            }
        }
        while (pre <= pre_hi && post <= post_hi) {
            uint32_t r = random_in_range(population_rng, i + 1);
            if (r < n_conns) {
                conns[r].pre = pre;
                conns[r].post = post;
            }
            fixed_total_next(&pre, &post, pre_lo, pre_hi);
            if (!obj->params.allow_self_connections && (pre == post)) {
                fixed_total_next(&pre, &post, pre_lo, pre_hi);
            }
            i++;
        }
        for (uint32_t i = 0; i < n_conns; i++) {
            uint32_t local_post = conns[i].post;
            if (local_post >= post_slice_start && local_post < post_slice_end) {
                local_post -= post_slice_start;
                uint32_t local_pre = conns[i].pre;
                accum weight = param_generator_generate(weight_generator);
                uint16_t delay = rescale_delay(
                        param_generator_generate(delay_generator), timestep_per_delay);
                if (!matrix_generator_write_synapse(matrix_generator, local_pre, local_post,
                        weight, delay, weight_scale)) {
                    // Not a lot we can do here...
                    log_error("Couldn't write matrix!");
                    return false;
                }
            }
        }
    }
    return true;
}
