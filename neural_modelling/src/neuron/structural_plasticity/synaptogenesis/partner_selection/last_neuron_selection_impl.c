#include "last_neuron_selection_impl.h"

spike_t* last_spikes_buffer[2];
uint32_t n_spikes[2];
uint32_t last_spikes_buffer_size;
uint32_t last_time;

void partner_init(uint8_t **data) {
    last_spikes_buffer_size = ((uint32_t *) *data)[0];
    for (uint32_t i = 0; i < 2; i++) {
        last_spikes_buffer[i] = (spike_t *) spin1_malloc(
            last_spikes_buffer_size * sizeof(spike_t));
        if (last_spikes_buffer[i] == NULL) {
            log_error("Out of memory when creating last spikes buffer");
            rt_error(RTE_SWERR);
        }
    }
    *data += sizeof(uint32_t);
}
