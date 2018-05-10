#include <stdbool.h>
#include <debug.h>
#include <delay_extension/delay_extension.h>
#include <synapse_expander/delay_sender.h>

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
#define MAX_DELAY 16
#define MAX_STAGE 9
#define PLASTIC_PLASTIC_SIZE 0
#define FIXED_FIXED_SIZE 1
#define FIXED_FIXED_OFFSET 2


uint32_t _build_static_word(
        uint32_t weight, uint32_t delay, uint32_t type,
        uint16_t post_index, uint32_t synapse_type_bits,
        uint32_t synapse_index_bits) {
    uint32_t synapse_index_mask = ((1 << synapse_index_bits) - 1);

    uint32_t wrd  = post_index & synapse_index_mask;
    wrd |= ((type & ((1 << synapse_type_bits) - 1)) << synapse_index_bits);
    wrd |= ((delay & SYNAPSE_DELAY_MASK) <<
            (synapse_index_bits + synapse_type_bits));
    wrd |= ((weight & SYNAPSE_WEIGHT_MASK) << SYNAPSE_WEIGHT_SHIFT);
    return wrd;
}

void matrix_generator_static_write_row(
        address_t synaptic_matrix,
        address_t delayed_synaptic_matrix,
        uint32_t n_pre_neurons, uint32_t pre_neuron_index,
        uint32_t max_row_length, uint32_t max_delayed_row_length,
        uint32_t synapse_type_bits, uint32_t synapse_index_bits,
        uint32_t synapse_type, uint32_t n_synapses,
        uint16_t *indices, int32_t *delays, int32_t *weights) {

    // Row address and position for each possible delay stage (including no
    // delay stage)
    address_t row_address[MAX_STAGE];
    address_t write_address[MAX_STAGE];
    row_address[0] =
        &(synaptic_matrix[pre_neuron_index * max_row_length]);
    write_address[0] = &(row_address[0][FIXED_FIXED_OFFSET]);
    address_t delayed_address =
        &(delayed_synaptic_matrix[pre_neuron_index * max_delayed_row_length]);
    uint32_t single_matrix_size = n_pre_neurons * max_delayed_row_length;
    for (uint32_t i = 1; i < MAX_STAGE; i++) {
        row_address[i] = &(delayed_address[single_matrix_size * (i - 1)]);
        write_address[i] = &(row_address[i][FIXED_FIXED_OFFSET]);
    }

    for (uint32_t synapse = 0; synapse < n_synapses; synapse++) {

        // Post-neuron index
        uint32_t post_index = indices[synapse];

        // Weight
        int32_t weight = weights[synapse];
        if (weight < 0) {
            weight = -weight;
        }

        // Delay
        int32_t delay = delays[synapse];
        if (delay < 1) {
            log_warning("Delay of %u is too small", delay);
            delay = 1;
        }
        uint32_t stage = (delay - 1) / MAX_DELAY;
        if (stage > MAX_STAGE) {
            log_warning("Delay of %u is too big", delay);
            stage = MAX_STAGE;
            delay = (stage * MAX_DELAY);
        }
        delay = ((delay - 1) % MAX_DELAY) + 1;
        if (stage > 0) {
            delay_sender_send(pre_neuron_index, stage - 1);
        }

        // Build synaptic word
        uint32_t word = _build_static_word(
            weight, delay, synapse_type, post_index, synapse_type_bits,
            synapse_index_bits);

        // Write the word
        address_t write_ptr = write_address[stage];
        *write_ptr++ = word;

        // Increment the size of the current row
        address_t size = &(row_address[stage][FIXED_FIXED_SIZE]);
        *size += 1;
    }
}
