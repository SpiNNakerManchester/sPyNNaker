#include <debug.h>
#include <spin1_api.h>
#include <common/neuron-typedefs.h>

#define SIZE_OF_SINGLE_FIXED_SYNAPSE 4

static uint32_t single_fixed_synapse[SIZE_OF_SINGLE_FIXED_SYNAPSE];

bool direct_synapses_initialise(
        address_t direct_matrix_address, address_t *direct_synapses_address){

    // Work out the positions of the direct and indirect synaptic matrices
    // and copy the direct matrix to DTCM
    uint32_t direct_matrix_size = direct_matrix_address[0];
    log_info("Direct matrix malloc size is %d", direct_matrix_size);

    if (direct_matrix_size != 0) {
        *direct_synapses_address = (address_t)spin1_malloc(direct_matrix_size);

        if (*direct_synapses_address == NULL) {
            log_error("Not enough memory to allocate direct matrix");
            return false;
        }
        log_debug(
            "Copying %u bytes of direct synapses to 0x%08x",
            direct_matrix_size, *direct_synapses_address);
        spin1_memcpy(
            *direct_synapses_address, &(direct_matrix_address[1]),
            direct_matrix_size);
    }

    // Set up for single fixed synapses (data that is consistent per direct row)
    single_fixed_synapse[0] = 0;
    single_fixed_synapse[1] = 1;
    single_fixed_synapse[2] = 0;

    return true;
}

synaptic_row_t direct_synapses_get_direct_synapse(address_t row_address){
    single_fixed_synapse[3] = (uint32_t) row_address[0];
    return (synaptic_row_t) single_fixed_synapse;
}
