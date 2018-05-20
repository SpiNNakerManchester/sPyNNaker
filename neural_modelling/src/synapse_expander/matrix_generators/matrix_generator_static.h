#include <stdbool.h>
#include <debug.h>
#include <delay_extension/delay_extension.h>
#include <synapse_expander/delay_sender.h>
#include "matrix_generator_common.h"

void *matrix_generator_static_initialize(address_t *region) {
    use(region);
    return NULL;
}

void matrix_generator_static_free(void *data) {
    use(data);
}

#define SYNAPSE_WEIGHT_SHIFT 16
#define SYNAPSE_WEIGHT_MASK 0xFFFF
#define SYNAPSE_DELAY_MASK 0xFF
#define STATIC_PLASTIC_PLASTIC_SIZE 0
#define STATIC_FIXED_PLASTIC_SIZE 2
#define STATIC_FIXED_FIXED_SIZE 1
#define STATIC_FIXED_FIXED_OFFSET 3


uint32_t _build_static_word(
        uint16_t weight, uint16_t delay, uint32_t type,
        uint16_t post_index, uint32_t synapse_type_bits,
        uint32_t synapse_index_bits) {
    uint32_t synapse_index_mask = ((1 << synapse_index_bits) - 1);

    uint32_t wrd  = post_index & synapse_index_mask;
    wrd |= ((type & ((1 << synapse_type_bits) - 1)) << synapse_index_bits);
    wrd |= ((delay & SYNAPSE_DELAY_MASK) <<
            (synapse_index_bits + synapse_type_bits));
    wrd |= ((weight & SYNAPSE_WEIGHT_MASK) << SYNAPSE_WEIGHT_SHIFT);
    log_info("Writing word 0x%08x (index_bits = %u, type_bits = %u", wrd, synapse_index_bits, synapse_type_bits);
    return wrd;
}

void matrix_generator_static_write_row(
        void *data,
        address_t synaptic_matrix, address_t delayed_synaptic_matrix,
        uint32_t n_pre_neurons, uint32_t pre_neuron_index,
        uint32_t max_row_length, uint32_t max_delayed_row_length,
        uint32_t synapse_type_bits, uint32_t synapse_index_bits,
        uint32_t synapse_type, uint32_t n_synapses,
        uint16_t *indices, uint16_t *delays, uint16_t *weights,
        uint32_t max_stage) {
    use(data);

    // Row address and position for each possible delay stage (including no
    // delay stage)
    address_t row_address[max_stage];
    row_address[0] = NULL;
    if (synaptic_matrix != NULL) {
        row_address[0] =
            &(synaptic_matrix[pre_neuron_index * (max_row_length + 3)]);
    }
    if (delayed_synaptic_matrix != NULL) {
        address_t delayed_address =
            &(delayed_synaptic_matrix[
                pre_neuron_index * (max_delayed_row_length + 3)]);
        uint32_t single_matrix_size =
            n_pre_neurons * (max_delayed_row_length + 3);
        for (uint32_t i = 1; i < max_stage; i++) {
            row_address[i] = &(delayed_address[single_matrix_size * (i - 1)]);
        }
    } else {
        for (uint32_t i = 1; i < max_stage; i++) {
            row_address[i] = NULL;
        }
    }
    address_t write_address[max_stage];
    for (uint32_t i = 0; i < max_stage; i++) {
        if (row_address[i] != NULL) {
            row_address[i][STATIC_FIXED_FIXED_SIZE] = 0;
            row_address[i][STATIC_PLASTIC_PLASTIC_SIZE] = 0;
            row_address[i][STATIC_FIXED_PLASTIC_SIZE] = 0;
            write_address[i] = &(row_address[i][STATIC_FIXED_FIXED_OFFSET]);
        } else {
            write_address[i] = NULL;
        }
    }

    for (uint32_t synapse = 0; synapse < n_synapses; synapse++) {

        // Post-neuron index
        uint32_t post_index = indices[synapse];

        // Weight
        uint16_t weight = weights[synapse];

        // Delay
        struct delay_value delay = get_delay(delays[synapse], max_stage);
        if (delay.stage > 0) {
            delay_sender_send(pre_neuron_index, delay.stage - 1);
        }
        if (write_address[delay.stage] == NULL) {
            log_error("Delay stage %u has not been initialised", delay.stage);
            rt_error(RTE_SWERR);
        }

        // Build synaptic word
        uint32_t word = _build_static_word(
            weight, delay.delay, synapse_type, post_index, synapse_type_bits,
            synapse_index_bits);

        // Write the word
        log_info("Writing to 0x%08x for stage %u", write_address[delay.stage], delay.stage);
        write_address[delay.stage][0] = word;
        write_address[delay.stage] = &(write_address[delay.stage][1]);

        // Increment the size of the current row
        log_info("Updating 0x%08x", row_address[delay.stage]);
        row_address[delay.stage][STATIC_FIXED_FIXED_SIZE] += 1;
    }
}
