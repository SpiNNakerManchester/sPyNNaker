#ifndef __SEND_SPIKE_H__
#define __SEND_SPIKE_H__

#include <stdint.h>
#include <stdbool.h>
// #include <tdma_processing.h>
#include <spin1_api_params.h>
#include "plasticity/synapse_dynamics.h"

static inline void send_spike_mc(uint32_t key) {
    while (cc[CC_TCR] & TX_FULL_MASK) {
        spin1_delay_us(1);
    }
    cc[CC_TCR] = PKT_MC;
    cc[CC_TXKEY]  = key;
}

extern uint32_t key;
extern bool use_key;
extern uint32_t earliest_send_time;
extern uint32_t latest_send_time;
static inline void send_spike(uint32_t timer_count, uint32_t time, uint32_t neuron_index) {
    // Do any required synapse processing
    synapse_dynamics_process_post_synaptic_event(time, neuron_index);

    if (use_key) {
//        tdma_processing_send_packet(
//            (key | neuron_index), 0, NO_PAYLOAD, timer_count);
        send_spike_mc(key | neuron_index);
        uint32_t clocks = tc[T1_COUNT];
        if (clocks > earliest_send_time) {
            earliest_send_time = clocks;
        }
        if (clocks < latest_send_time) {
            latest_send_time = clocks;
        }
    }
}

#endif // __SEND_SPIKE_H__
