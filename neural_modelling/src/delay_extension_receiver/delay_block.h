#ifndef _DELAY_BLOCK_H_
#define _DELAY_BLOCK_H_

#include <bit_field.h>
#include <debug.h>
#include <spin1_api.h>
#include <string.h> //memset <= should not be here! nostdlib

typedef struct delay_msg_t{
    uint8_t source_neuron_id;
    uint8_t delay;
} delay_msg_t;


bool init_delay_block(uint32_t num_delay_stages, uint32_t neuron_bit_field_words,
                      bit_field_t* *delay_block);
bool init_spike_counters(uint32_t num_delay_slots_pot, uint32_t num_neurons,
                         uint8_t** *spike_counters);
bool add_delay(uint32_t source_id, uint32_t stage, bit_field_t* *delay_block);

#endif //_DELAY_BLOCK_H_

