/**
 *! \file
 *! \brief Fixed-Number-Post (fan-out) Connection generator implementation
 *!        Each post-neuron is connected to exactly n_pre pre-neurons (chosen at random)
 */

#include <log.h>
#include <synapse_expander/rng.h>

/**
 *! \brief The parameters that can be copied from SDRAM
 */
struct fixed_post_params {
    uint32_t allow_self_connections;
    uint32_t with_replacement;
    uint32_t n_post;
    uint32_t n_post_neurons;
};

/**
 *! \brief The data to be passed around.  This includes the parameters, and the
 *!        RNG of the connector
 */
struct fixed_post {
    struct fixed_post_params params;
    rng_t rng;
};

void *connection_generator_fixed_post_initialise(address_t *region) {

    // Allocate memory for the parameters
    struct fixed_post *params = (struct fixed_post *) spin1_malloc(
        sizeof(struct fixed_post));

    // Copy the parameters in
    address_t params_sdram = *region;
    spin1_memcpy(
        &(params->params), params_sdram, sizeof(struct fixed_post_params));
    params_sdram = &(params_sdram[sizeof(struct fixed_post_params) >> 2]);

    // Initialise the RNG
    params->rng = rng_init(&params_sdram);
    *region = params_sdram;
    log_debug(
        "Fixed Number Post Connector, allow self connections = %u, "
        "with replacement = %u, n_post = %u, "
        "n post neurons = %u", params->params.allow_self_connections,
        params->params.with_replacement, params->params.n_post,
		params->params.n_post_neurons);
    return params;
}

void connection_generator_fixed_post_free(void *data) {
    sark_free(data);
}

uint32_t connection_generator_fixed_post_generate(
        void *data, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(pre_slice_start);
    use(pre_slice_count);

    // If there are no connections to be made, return 0

    // Don't think that this is necessary, unless the user says 0 for some reason?
    struct fixed_post *params = (struct fixed_post *) data;
    if (max_row_length == 0 || params->params.n_post == 0) {
        return 0;
    }

    // Get how many values can be sampled from
    uint32_t n_values = params->params.n_post_neurons;

    // Get the number of connections on this row
    uint32_t n_conns = params->params.n_post;

    log_debug("Generating %u from %u possible synapses", n_conns, n_values);

    uint16_t full_indices[n_conns];
    // Sample from the possible connections in this section n_conns times
    if (params->params.with_replacement) {
        // Sample them with replacement
    	if (params->params.allow_self_connections) {
    		// self connections are allowed so sample
    		for (unsigned int i = 0; i < n_conns; i++) {
        		uint32_t u01 = (rng_generator(params->rng) & 0x00007fff);
        		uint32_t j = (u01 * n_values) >> 15;
        		full_indices[i] = j;
        	}
    	} else {
    		// self connections are not allowed (on this slice)
    		for (unsigned int i = 0; i < n_conns; i++) {
    			// Set j to the disallowed value, then test against it
    			uint32_t j = pre_neuron_index;

    			do {
    				uint32_t u01 = (rng_generator(params->rng) & 0x00007fff);
    				j = (u01 * n_values) >> 15;
    			} while (j == pre_neuron_index);

    			full_indices[i] = j;
    		}
        }
    } else {
        // Sample them without replacement using reservoir sampling
    	if (params->params.allow_self_connections) {
    		// Self-connections are allowed so do this normally
    		for (unsigned int i = 0; i < n_conns; i++) {
    			full_indices[i] = i;
    		}
    		// And now replace values if chosen at random to be replaced
    		for (unsigned int i = n_conns; i < n_values; i++) {
    			// j = random(0, i) (inclusive)
    			const unsigned int u01 = (rng_generator(params->rng) & 0x00007fff);
    			const unsigned int j = (u01 * (i + 1)) >> 15;
    			if (j < n_conns) {
    				full_indices[j] = i;
    			}
    		}
    	} else {
    		// Self-connections are not allowed
    		for (unsigned int i = 0; i < n_conns; i++) {
    			if (i == pre_neuron_index) {
    				// set to a value not equal to i for now
    				full_indices[i] = n_conns;
    			} else {
    				full_indices[i] = i;
    			}
    		}
    		// And now "replace" values if chosen at random to be replaced
    		for (unsigned int i = n_conns; i < n_values; i++) {
    			// Set j to the disallowed value, then test against it
    			unsigned int j = pre_neuron_index;

    			do {
        			// j = random(0, i) (inclusive)
    				const unsigned int u01 = (rng_generator(params->rng) & 0x00007fff);
    				j = (u01 * (i + 1)) >> 15;
    			} while (j == pre_neuron_index);

    			if (j < n_conns) {
    				full_indices[j] = i;
    			}
    		}
    	}
    }

    // Loop over the full indices array, and only keep indices on this post-slice
    uint32_t count_indices = 0;
    for (unsigned int i = 0; i < n_conns; i++) {
    	uint32_t j = full_indices[i];
    	if ((j >= post_slice_start) && (j < post_slice_start + post_slice_count)) {
    		indices[count_indices] = j - post_slice_start; // On this slice!
    		count_indices += 1;
    	}
    }

//    // Double-check for debug purposes
//    for (unsigned int i = 0; i < count_indices; i++) {
//    	log_info("Check: indices[%u] is %u", i, indices[i]);
//    }
//    log_info("pre_neuron_index is %u count_indices is %u", pre_neuron_index, count_indices);

    return count_indices;
}
