#include "delay_block.h"

bool init_delay_block(uint32_t num_delay_stages, uint32_t neuron_bit_field_words,
                      bit_field_t* *delay_block){
    log_info("\tAllocating delay block memory");
    bit_field_t *dly_blk = NULL;
    dly_blk = (bit_field_t*) spin1_malloc(num_delay_stages * sizeof(bit_field_t));
    if (dly_blk == NULL){
        log_error("\tUnable to allocate memory for delay stages");
        return false;
    }

    // Loop through delay stages
    for (uint32_t d = 0; d < num_delay_stages; d++) {
        log_debug("\t delay stage %u", d);

        // Allocate bit-field
        dly_blk[d] = (bit_field_t) spin1_malloc(
                                   neuron_bit_field_words * sizeof(uint32_t));

        if( dly_blk[d] == NULL ){
            log_error("\tUnable to allocate memory for a delay stage %d", d);
            return false;
        }

        log_debug("\tClearing delay stage %d bit field",d);
        clear_bit_field(dly_blk[d], neuron_bit_field_words);
        use(dly_blk[d]);
    }
    *delay_block = dly_blk;
    log_info("\tdelay block address 0x%08x", *delay_block);
    return true;
}


bool init_spike_counters(uint32_t num_delay_slots_pot, uint32_t num_neurons,
                         uint8_t** *spike_counters){

    log_info("\tAllocate array of counters for each delay slot");
    uint8_t **spk_cnt = NULL;
    spk_cnt = (uint8_t**) spin1_malloc(
        num_delay_slots_pot * sizeof(uint8_t*));

    if (spk_cnt == NULL){
        log_error("\tUnable to allocate memory for spike counters");
        return false;
    }
    for (uint32_t s = 0; s < num_delay_slots_pot; s++) {
        log_debug("\tspike counter %d", s);
        // Allocate an array of counters for each neuron and zero
        spk_cnt[s] = (uint8_t*) spin1_malloc(
            num_neurons * sizeof(uint8_t));
        memset(spk_cnt[s], 0, num_neurons * sizeof(uint8_t));
        if (spk_cnt[s] == NULL){
            log_error("\tUnable to allocate memory for spike counter %d", s);
            return false;
        }
        // make sure optimization doesn't remove memset
        use(spk_cnt[s]);
    }

    *spike_counters = spk_cnt;
    log_info("\tspike counters address 0x%08x", *spike_counters);

    return true;
}

bool add_delay(uint32_t source_id, uint32_t stage, bit_field_t* *delay_block){
    if (*delay_block == NULL){
        log_error("\tadd_delay: Delay Block not initialized");
        return false;
    }

    bit_field_set((*delay_block)[stage], source_id);
    return true;
}
