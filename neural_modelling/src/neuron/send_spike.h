#ifndef __SEND_SPIKE_H__
#define __SEND_SPIKE_H__

#include <stdint.h>
#include <stdbool.h>
#include <tdma_processing.h>
#include "plasticity/synapse_dynamics.h"

extern uint32_t key;
extern bool use_key;
static inline void send_spike(uint32_t timer_count, uint32_t time, uint32_t neuron_index) {
    // Do any required synapse processing
    synapse_dynamics_process_post_synaptic_event(time, neuron_index);

    if (use_key) {
        tdma_processing_send_packet(
            (key | neuron_index), 0, NO_PAYLOAD, timer_count);
    }
}

#endif // __SEND_SPIKE_H__
