#include <stdbool.h>
#include <debug.h>

bool matrix_generator_static_is_static(void *data) {
    use(data);
    return true;
}

void *matrix_generator_static_initialize() {
    return NULL;
}

#define SYNAPSE_WEIGHT_SHIFT 16
#define SYNAPSE_WEIGHT_MASK 0xFFFF
#define SYNAPSE_DELAY_MASK 0xFF
#define MAX_DELAY 16

int32_t _clamp_delay(int32_t delay);
int32_t _clamp_weight(int32_t weight);


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

uint32_t matrix_generator_static_write_row(
        address_t synapse_mtx,
        uint32_t num_pre_neurons, uint32_t pre_idx,
        uint32_t max_per_pre_matrix_size,
        uint32_t numIndices,
        uint32_t syn_type_bits, uint32_t words_per_weight,
        uint32_t max_num_plastic,uint32_t max_num_static, uint32_t synapseType,
        uint16_t *indices, int32_t *delays, int32_t *weights,
        uint32_t synapse_index_bits, bool is_signed_weight) {
    use(words_per_weight);

    uint32_t fixed_mask = ((1 << (syn_type_bits + synapse_index_bits)) - 1);
    uint32_t inserted_indices = 0;
    uint32_t min_indices =
            max_num_static < numIndices ? max_num_static : numIndices;
    uint8_t first_pass = 1;
    uint32_t preIndex = pre_idx;
    uint32_t delay_stage_pos[9];

    for (uint16_t data_index = 0; data_index < numIndices; data_index++) {
        // Extract index pointed to by sorted index
        const uint32_t postIndex = indices[data_index];

        // EXC == 0, INH == 1
        int32_t weight = weights[data_index];

        // if(weight == 0){ continue; }

        log_debug("pre, post, w => %u, %u, %k", pre_idx, postIndex, weight);

        if (is_signed_weight && weight < 0
                && (synapseType == 0 || synapseType == 1)) {
            synapseType = 1;
            weight = -weight;
        }
        weight = _clamp_weight(weight);

        // Clamp delays and weights pointed to be sorted index
        int32_t delay = _clamp_delay(delays[data_index]);

        uint32_t stage = (delay - 1) / MAX_DELAY;
        delay = ((delay - 1) % MAX_DELAY) + 1;
        preIndex = pre_idx + (stage * num_pre_neurons);

        // Build synaptic word
        uint32_t word = _build_static_word(
            weight, delay, synapseType, postIndex, syn_type_bits,
            synapse_index_bits);

        log_debug("%u,", word);

        address_t start_of_static = synapse_mtx + 1
            + preIndex * (max_per_pre_matrix_size);

        //    TODO: should I set this?
        if (first_pass) {
            //      *start_of_static = *start_of_static + max_num_static;
            //how many indices where generated on machine
            *start_of_static = *start_of_static + min_indices;
            if (*start_of_static > max_num_static) {
                *start_of_static = max_num_static;
            }
            //    *start_of_static = max_num_static;
        }

        start_of_static += 2;

        // Write word to matrix
        //0 <- plastic-plastic word
        //NULL <- start of plastic-plastic region,
        //false <- not a plastic synapse
        insert_sorted(word, start_of_static, fixed_mask, max_num_static, 0,
            NULL, 1, false, false);
        first_pass = 0;
        inserted_indices++;
        if (inserted_indices == max_num_static) {
            break;
        }
    }

    log_debug("\n");

    // Return number of words written to row
    return 1;
}
