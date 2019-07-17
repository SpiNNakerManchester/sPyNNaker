#include "last_neuron_selection_impl.h"

spike_t* last_spikes_buffer[2];
uint32_t n_spikes[2];
uint32_t last_spikes_buffer_size;
uint32_t last_time;

address_t partner_init(address_t data) {
    last_spikes_buffer_size = data[0];
    return &data[1];
}
