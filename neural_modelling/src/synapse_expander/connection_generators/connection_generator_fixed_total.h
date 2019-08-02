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
 *! \brief Fixed-Total-Number (Multapse) Connection generator implementation
 */

#include <log.h>
#include <synapse_expander/rng.h>
#include <synapse_expander/generator_types.h>

static initialize_func connection_generator_fixed_total_initialise;
static free_func connection_generator_fixed_total_free;
static generate_connection_func connection_generator_fixed_total_generate;

/**
 *! \brief The parameters that can be copied from SDRAM
 */
struct fixed_total_params {
    uint32_t allow_self_connections;
    uint32_t with_replacement;
    uint32_t n_connections;
    uint32_t n_potential_synapses;
};

/**
 *! \brief The data to be passed around.  This includes the parameters, and the
 *!        RNG of the connector
 */
struct fixed_total {
    struct fixed_total_params params;
    rng_t rng;
};

static void *connection_generator_fixed_total_initialise(address_t *region) {
    // Allocate memory for the parameters
    struct fixed_total *obj = spin1_malloc(sizeof(struct fixed_total));

    // Copy the parameters in
    struct fixed_total_params *params_sdram = (void *) *region;
    obj->params = *params_sdram++;
    *region = (void *) params_sdram;

    // Initialise the RNG
    obj->rng = rng_init(region);
    log_debug("Fixed Total Number Connector, allow self connections = %u, "
            "with replacement = %u, n connections = %u, "
            "n potential connections = %u",
            obj->params.allow_self_connections,
            obj->params.with_replacement, obj->params.n_connections,
            obj->params.n_potential_synapses);
    return obj;
}

static void connection_generator_fixed_total_free(void *data) {
    struct fixed_total *params = data;
    rng_free(params->rng);
    sark_free(data);
}

/**
 *! \brief Draw from a binomial distribution i.e. with replacement
 *! \param[in] n The number of times the experiment is run
 *! \param[in] N The number of items in the bag
 *! \param[in] K The number of items that are valid
 *! \param[in] rng The uniform random number generator
 *! \return The number of times a valid item was drawn
 */
static uint32_t binomial(uint32_t n, uint32_t N, uint32_t K, rng_t rng) {
    uint32_t count = 0;
    uint32_t not_K = N - K;
    for (uint32_t i = 0; i < n; i++) {
        unsigned long fract value = ulrbits(rng_generator(rng));
        uint32_t pos = (uint32_t) (value * (K + not_K));
        if (pos < K) {
            count++;
        }
    }
    return count;
}

/**
 * \brief Draw from a hyper-geometric distribution i.e. without replacement
 * \param[in] n The number of times the experiment is run
 * \param[in] N The number of items in the bag at the start
 * \param[in] K The number of valid items in the bag at the start
 * \param[in] rng The uniform random number generator
 * \return The number of times a valid item was drawn
 */
static uint32_t hypergeom(uint32_t n, uint32_t N, uint32_t K, rng_t rng) {
    uint32_t count = 0;
    uint32_t K_remaining = K;
    uint32_t not_K_remaining = N - K;
    for (uint32_t i = 0; i < n; i++) {
        unsigned long fract value = ulrbits(rng_generator(rng));
        uint32_t pos = (uint32_t) (value * (K_remaining + not_K_remaining));
        if (pos < K_remaining) {
            count++;
            K_remaining--;
        } else {
            not_K_remaining--;
        }
    }
    return count;
}

static uint32_t connection_generator_fixed_total_generate(
        void *data, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(pre_slice_start);

    // If there are no connections left or none to be made, return 0
    struct fixed_total *obj = data;
    if (max_row_length == 0 || obj->params.n_connections == 0) {
        return 0;
    }

    // Work out how many values can be sampled from
    uint32_t n_values = post_slice_count;
    if (!obj->params.allow_self_connections
            && pre_neuron_index >= post_slice_start
            && pre_neuron_index < (post_slice_start + post_slice_count)) {
        n_values--;
    }
    uint32_t n_conns = 0;

    // If we're on the last row of the sub-matrix, then all of the remaining
    // sub-matrix connections get allocated to this row
    if (pre_neuron_index == (pre_slice_start + pre_slice_count - 1)) {
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
        if (pre_neuron_index == (pre_slice_start + pre_slice_count - 1)) {
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
            uint32_t j = (u01 * post_slice_count) >> 15;
            indices[i] = j;
        }
    } else {
        // Sample them without replacement using reservoir sampling
        for (unsigned int i = 0; i < n_conns; i++) {
            indices[i] = i;
        }
        for (unsigned int i = n_conns; i < post_slice_count; i++) {
            // j = random(0, i) (inclusive)
            const unsigned int u01 = rng_generator(obj->rng) & 0x00007fff;
            const unsigned int j = (u01 * (i + 1)) >> 15;
            if (j < n_conns) {
                indices[j] = i;
            }
        }
    }

    obj->params.n_connections -= n_conns;
    obj->params.n_potential_synapses -= post_slice_count;

    return n_conns;
}
