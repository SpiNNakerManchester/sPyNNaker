#include "matrix_generator.h"
#include <spin1_api.h>
#include <debug.h>

#include "matrix_generators/matrix_generator_static.h"

#define N_MATRIX_GENERATORS 1
#define MAX_DELAY 16

#define _pack_id_delay(i, d) ((i & 0xFF) | ((d & 0xFF) << 8))

struct matrix_generator {
    uint32_t index;
    uint32_t n_pre_state_words;
    bool is_signed_weights;
    void *data;
};

struct matrix_generator_info {
    uint32_t hash;
    void* (*initialize)(address_t *region);
    bool (*is_static)();
    uint32_t (*write_row)(
        address_t synapse_mtx,
        uint32_t num_pre_neurons, uint32_t pre_idx,
        uint32_t max_per_pre_matrix_size,
        uint32_t numIndices,
        uint32_t syn_type_bits, uint32_t words_per_weight,
        uint32_t max_num_plastic, uint32_t max_num_static, uint32_t synapseType,
        uint16_t *indices, int32_t *delays, int32_t *weights);
};

struct matrix_generator_info *matrix_generators[N_MATRIX_GENERATORS];

matrix_generator_t matrix_generator_init(uint32_t hash, address_t *in_region) {

    for (uint32_t i = 0; i < N_MATRIX_GENERATORS; i++) {
        if (hash == matrix_generators[i]->hash) {

            address_t region = *in_region;
            matrix_generator_t generator = spin1_malloc(
                sizeof(matrix_generator_t));
            if (generator == NULL) {
                log_error("Could not create generator");
                return NULL;
            }
            generator->index = i;
            generator->n_pre_state_words = *region++;
            generator->is_signed_weights = *region++;
            generator->data = matrix_generators[i]->initialize(&region);
            *in_region = region;
            return generator;
        }
    }
    log_error("Matrix generator with hash %u not found", hash);
    return NULL;
}

bool matrix_generator_is_static(matrix_generator_t generator) {
    return matrix_generators[generator->index]->is_static();
}

uint32_t matrix_generator_n_pre_state_words(matrix_generator_t generator) {
    return generator->n_pre_state_words;
}

int32_t _clamp_delay(int32_t delay) {

    // If delay is lower than minimum (1 timestep), clamp
    return (delay < 1) ? 1 : delay;
}

int32_t _clamp_weight(int32_t weight) {
    return weight & 0xFFFF;
}

void insert_sorted(T new_fixed, T *fixed_address, T val_mask, uint32_t max_rows,
        uint16_t new_plastic = 0, uint16_t *plastic_address = NULL,
        uint32_t plastic_step = 1,
        bool is_plastic = false, bool skip_first = false) {

    if (*fixed_address == EMPTY_VAL && !skip_first) {
        *fixed_address = new_fixed;

        if(is_plastic) {plastic_address[plastic_step-1] = new_plastic;}
        return;
    }
    for(uint32_t i = 1; i < max_rows; i++) {
        if ((fixed_address[i] == EMPTY_VAL) &&
                (fixed_address[i - 1] & val_mask) <
                (new_fixed & val_mask)) {

            fixed_address[i] = new_fixed;

            if(is_plastic) {
                plastic_address[plastic_step*(i+1) - 1] = new_plastic;
            }
//            LOG_PRINT(LOG_LEVEL_INFO, "\tinserted in %u", i);
            return;
        } else if ((fixed_address[i] == EMPTY_VAL) &&
                (fixed_address[i - 1] & val_mask) >
                (new_fixed & val_mask)) {

            fixed_address[i] = fixed_address[i - 1];
            fixed_address[i - 1] = new_fixed;

            if(is_plastic) {
                plastic_address[plastic_step*(i+1) - 1] =
                plastic_address[plastic_step*i - 1];
                plastic_address[plastic_step*i - 1] = new_plastic;
            }
            log_debug("\tinserted in %u", i);
            return;
        } else if ((fixed_address[i - 1] & val_mask) >
                (new_fixed & val_mask)) {

            swap(fixed_address[i-1], new_fixed);
            if(is_plastic) {
                swap(plastic_address[plastic_step*(i - 1)], new_plastic);
            }
        }
    }
}

bool matrix_generator_generate(
        matrix_generator_t generator, address_t synaptic_matrix_address,
        uint32_t address_delta, uint32_t max_n_static, uint32_t max_n_plastic,
        uint32_t max_per_pre_matrix_size, uint32_t synapse_type,
        uint32_t post_slice_start, uint32_t post_slice_count,
        uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_block_start, uint32_t pre_block_count,
        uint32_t words_per_weight, int32_t *weight_scales,
        uint32_t n_synapse_bits, connection_generator_t connection_generator,
        param_generator_t delay_generator, param_generator_t weight_generator,
        rng_t rng, uint16_t *pre_delay_pairs, uint16_t *pair_count) {
    log_debug(
            "\tGenerating (%u, %u)(%u:%u) => (%u:%u)",
            pre_slice_start, pre_slice_start + pre_slice_count - 1,
            pre_block_start, pre_block_start + pre_block_count - 1,
            post_slice_start, post_slice_start + post_slice_count - 1);

    uint32_t max_indices = max_n_plastic + max_n_static;
    *pair_count = 0;

    address_t ind_syn_mtx = &(synaptic_matrix_address[1]);
    uint32_t total_conns = 0;
    for (uint32_t pre_idx = pre_block_start;
            pre_idx < (pre_block_start + pre_block_count); pre_idx++) {

        uint16_t indices[512];
        log_debug("\t\t\t\tGenerating indices-------------------------");
        const uint32_t numIndices = connection_generator_generate(
            connection_generator, pre_block_start, pre_block_count, pre_idx,
            post_slice_start, post_slice_count, max_indices, rng, indices);
        log_debug("\t\t\t\t%u indices", numIndices);

        // TraceUInt(indices, numIndices);

        // Generate delays for each index
        int32_t delays[512];
        log_debug("\t\t\t\tGenerating delays-------------------------");
        param_generator_generate(
            delay_generator, numIndices, 0, pre_idx, post_slice_start, indices,
            rng, delays);
        // TraceUInt(delays, numIndices);

        // Generate weights for each index
        int32_t weights[512];
        log_info("\t\t\t\tGenerating weights------------------------");

        // STATIC == 0, PLASTIC == 1
        param_generator_generate(
            weight_generator, numIndices, weight_scales[synapse_type], pre_idx,
            post_slice_start, indices, rng, weights);
        // TraceUInt(weights, numIndices);

        for (uint32_t idx = 0; idx < numIndices; idx++) {
            pre_delay_pairs[*pair_count] = 0;
            uint32_t d = _clamp_delay(delays[idx]);
            if (d > MAX_DELAY) {
                log_debug("pre = %u, delay = %u", pre_idx, d);
                pre_delay_pairs[*pair_count] = _pack_id_delay(pre_idx, d);
                (*pair_count)++;
            }

        }

        // pre_idx += pre_start;

        // Write row
        matrix_generators[generator->index]->write_row(
            ind_syn_mtx + address_delta, pre_slice_count,
            pre_idx - pre_slice_start, max_per_pre_matrix_size,
            numIndices, n_synapse_bits, words_per_weight,
            max_n_plastic, max_n_static, synapse_type, indices, delays,
            weights);

        if (pre_idx % 1 == 0 && numIndices > 0) {
            log_debug("\t\tGenerated %u synapses for %u, addr delta %u",
                    numIndices, pre_idx, address_delta);
        }
        total_conns += numIndices;
    }
    log_debug("\t\tTotal synapses generated = %u . Done!",
            total_conns);

    //TODO: add support for direct matrices
    //direct synapse matrix not supported yet!
    *(synaptic_matrix_address + (*synaptic_matrix_address >> 2) + 1) = 0;
    return true;
}

void register_matrix_generators() {

}
