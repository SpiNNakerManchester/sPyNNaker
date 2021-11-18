#include "weight_pfpc_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_weight_region_data_t *plasticity_weight_region_data;
uint32_t *weight_shift;

typedef struct {
    accum min_weight;
    accum max_weight;
    accum a2_plus;
    accum a2_minus;
} pfpc_config_t;

//---------------------------------------
// Functions
//---------------------------------------
address_t weight_initialise(
        address_t address, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {

	io_printf(IO_BUF, "PFPC weight_initialise: starting\n");
	io_printf(IO_BUF, "\tSTDP multiplicative weight dependence\n");

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof

    plasticity_weight_region_data_t *dtcm_copy = plasticity_weight_region_data =
        spin1_malloc(sizeof(plasticity_weight_region_data_t) * n_synapse_types);

    if (dtcm_copy == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }
    weight_shift = spin1_malloc(sizeof(uint32_t) * n_synapse_types);
    if (weight_shift == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }

    pfpc_config_t *config = (pfpc_config_t *) address;
    for (uint32_t s = 0; s < n_synapse_types; s++) {
        // Copy parameters
        dtcm_copy[s].min_weight = config->min_weight;
        dtcm_copy[s].max_weight = config->max_weight;
        dtcm_copy[s].a2_plus = config->a2_plus;
        dtcm_copy[s].a2_minus = config->a2_minus;

        // Get the weight shift for switching from int16 to accum
        weight_shift[s] = ring_buffer_to_input_buffer_left_shifts[s];

        io_printf(IO_BUF,
            "\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d,"
            " Weight multiply right shift:%u\n",
            s, dtcm_copy[s].min_weight, dtcm_copy[s].max_weight,
            dtcm_copy[s].a2_plus, dtcm_copy[s].a2_minus, weight_shift[s]);
    }

    io_printf(IO_BUF, "PFPC weight_initialise: completed successfully");

    // Return end address of region
    return (address_t) config;
}
