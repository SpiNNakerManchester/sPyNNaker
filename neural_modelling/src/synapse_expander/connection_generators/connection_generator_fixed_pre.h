/**
 *! \file
 *! \brief Fixed-Number-Pre (fan-in) Connection generator implementation
 *!        Each post-neuron is connected to exactly n pre-neurons (chosen at random)
 */

#include <log.h>
#include <synapse_expander/rng.h>

/**
 *! \brief The parameters that can be copied from SDRAM
 */
struct fixed_pre_params {
    uint32_t allow_self_connections;
    uint32_t with_replacement;
    uint32_t n_pre;
    uint32_t n_pre_neurons;
};

/**
 *! \brief The data to be passed around.  This includes the parameters, and the
 *!        RNG of the connector
 */
struct fixed_pre {
    struct fixed_pre_params params;
    rng_t rng;
};

// A global 2d array containing the indices for each column
uint16_t** full_indices = NULL;

void *connection_generator_fixed_pre_initialise(address_t *region) {

    // Allocate memory for the parameters
    struct fixed_pre *params = (struct fixed_pre *) spin1_malloc(
        sizeof(struct fixed_pre));

    // Copy the parameters in
    address_t params_sdram = *region;
    spin1_memcpy(
        &(params->params), params_sdram, sizeof(struct fixed_pre_params));
    params_sdram = &(params_sdram[sizeof(struct fixed_pre_params) >> 2]);

    // Initialise the RNG
    params->rng = rng_init(&params_sdram);
    *region = params_sdram;
//    log_debug(
    log_info(
        "Fixed Total Number Connector, allow self connections = %u, "
        "with replacement = %u, n_pre = %u, "
        "n pre neurons = %u", params->params.allow_self_connections,
        params->params.with_replacement, params->params.n_pre,
        params->params.n_pre_neurons);
    return params;
}

void connection_generator_fixed_pre_free(void *data) {
    sark_free(data);
}

uint32_t connection_generator_fixed_pre_generate(
        void *data, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(pre_slice_start);
    use(pre_slice_count);

    // If there are no connections to be made, return 0

    // Don't think that this is necessary, unless the user says 0 for some reason?
    struct fixed_pre *params = (struct fixed_pre *) data;
    if (max_row_length == 0 || params->params.n_pre == 0) {
        return 0;
    }

    // THIS IS THE FIXED PRE NUMBER CONNECTOR... and this algorithm goes row-by-row
    // So the question is whether it's possible to "reverse-engineer" the post connector
    // to do something similar...

    // OK, so it's possible to do this...


	// Get how many values can be sampled from
	uint32_t n_values = params->params.n_pre_neurons;

	// Get the number of connections in this column
	uint32_t n_conns = params->params.n_pre;

	log_debug("Generating %u from %u possible synapses", n_conns, n_values);

	// The number of columns is the number of post-slices to do the calculation for
	uint32_t n_columns = post_slice_count;
    // If we're on the first row then do the calculations by looping over
	// the post-slices available here

	if (pre_neuron_index == 0) {
	    // Allocate array for each column (i.e. post-slice on this slice)
	    full_indices = (uint16_t**) spin1_malloc(
	        n_columns * sizeof(uint16_t*));
	    for (uint32_t n = 0; n < n_columns; n++) {
	        // Allocate an array of size n_pre for each column
	        full_indices[n] = (uint16_t*) spin1_malloc(
	            n_conns * sizeof(uint16_t));
	    }

	    // Loop over the columns and fill the full_indices array accordingly
	    for (uint32_t n = 0; n < n_columns; n++) {
	    	// Sample from the possible connections in this column n_conns times
	    	if (params->params.with_replacement) {
	    		// Sample them with replacement
	    		if (params->params.allow_self_connections) {
	    			// self connections are allowed so sample
	    			for (unsigned int i = 0; i < n_conns; i++) {
	    				uint32_t u01 = (rng_generator(params->rng) & 0x00007fff);
	    				uint32_t j = (u01 * n_values) >> 15;
	    				full_indices[n][i] = j;
	    			}
	    		} else {
	    			// self connections are not allowed (on this slice)
	    			for (unsigned int i = 0; i < n_conns; i++) {
	    				// Set j to the disallowed value, then test against it
	    				uint32_t j = n + post_slice_start;

	    				do {
	    					uint32_t u01 = (rng_generator(params->rng) & 0x00007fff);
	    					j = (u01 * n_values) >> 15;
	    				} while (j == (n + post_slice_start));

	    				full_indices[n][i] = j;
	    			}
	    		}
	    	} else {
	    		// Sample them without replacement using reservoir sampling
	    		if (params->params.allow_self_connections) {
	    			// Self-connections are allowed so do this normally
	    			for (unsigned int i = 0; i < n_conns; i++) {
	    				full_indices[n][i] = i;
	    			}
	    			// And now replace values if chosen at random to be replaced
	    			for (unsigned int i = n_conns; i < n_values; i++) {
	    				// j = random(0, i) (inclusive)
	    				const unsigned int u01 = (rng_generator(params->rng) & 0x00007fff);
	    				const unsigned int j = (u01 * (i + 1)) >> 15;
	    				if (j < n_conns) {
	    					full_indices[n][j] = i;
	    				}
	    			}
	    		} else {
	    			// Self-connections are not allowed
	    			for (unsigned int i = 0; i < n_conns; i++) {
	    				if (i == n + post_slice_start) {
	    					// set to a value not equal to i for now
	    					full_indices[n][i] = n_conns;
	    				} else {
	    					full_indices[n][i] = i;
	    				}
	    			}
	    			// And now "replace" values if chosen at random to be replaced
	    			for (unsigned int i = n_conns; i < n_values; i++) {
	    				// Set j to the disallowed value, then test against it
	    				unsigned int j = n + post_slice_start;

	    				do {
	    					// j = random(0, i) (inclusive)
	    					const unsigned int u01 = (rng_generator(params->rng) & 0x00007fff);
	    					j = (u01 * (i + 1)) >> 15;
	    				} while (j == n + post_slice_start);

	    				if (j < n_conns) {
	    					full_indices[n][j] = i;
	    				}
					}
				}
			}
		}
    }

    // Loop over the full indices array, and only keep indices on this post-slice
    uint32_t count_indices = 0;
    for (unsigned int i = 0; i < n_conns; i++) {
    	uint32_t j = full_indices[pre_neuron_index][i];
   		log_info("full_indices[%u][%u] = %u", pre_neuron_index, i, j);
    	if ((j >= post_slice_start) && (j < post_slice_start + post_slice_count)) {
    		indices[count_indices] = j - post_slice_start; // On this slice!
   			count_indices += 1;
   		}
    }

    // Double-check for debug purposes
    for (unsigned int i = 0; i < count_indices; i++) {
    	log_info("Check: indices[%u] is %u", i, indices[i]);
    }
    log_info("pre_neuron_index is %u count_indices is %u", pre_neuron_index, count_indices);

    return count_indices;
}
