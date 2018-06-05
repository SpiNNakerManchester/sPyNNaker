#include "connection_generator.h"
#include "param_generator.h"
#include "matrix_generators/matrix_generator_common.h"

#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>
#include <delay_extension/delay_extension.h>
#include <bit_field.h>

#define _unused(x) ((void)(x))

uint32_t max_matrix_size(uint32_t max_n_static, uint32_t max_n_plastic,
        uint32_t plastic_header) {
    // both plastic-plastic and plastic-fixed are 16-bit data

    uint32_t plastic_word_size = (max_n_plastic / 2) + (max_n_plastic % 2);
    log_debug("header: %u, static: %u, plastic: %u ; %u, def: 3",
        plastic_header, max_n_static, max_n_plastic, plastic_word_size);

    return 1 + plastic_header + max_n_plastic + 1 + 1 + max_n_static
        + plastic_word_size;

    // n_plastic was already multiplied before
    // return 1 + plastic_word_size + 1 + 1 + n_static + n_plastic;
}

bool read_delay_builder_region(address_t *in_region,
        bit_field_t *neuron_delay_stage_config, uint32_t pre_slice_start,
        uint32_t pre_slice_count) {

    address_t region = *in_region;

    const uint32_t max_row_n_synapses = *region++;
    const uint32_t max_delayed_row_n_synapses = *region++;
    const uint32_t post_slice_start = *region++;
    const uint32_t post_slice_count = *region++;
    const uint32_t max_stage = *region++;
    accum timestep_per_delay;
    spin1_memcpy(&timestep_per_delay, region++, sizeof(accum));

    const uint32_t connector_type_hash = *region++;
    const uint32_t delay_type_hash = *region++;

    // Generate matrix, connector, delays and weights

    connection_generator_t connection_generator =
        connection_generator_init(connector_type_hash, &region);
    param_generator_t delay_generator =
        param_generator_init(delay_type_hash, &region);

    *in_region = region;

    // If any components couldn't be created return false
    if (connection_generator == NULL || delay_generator == NULL) {
        return false;
    }

    uint32_t pre_slice_end = pre_slice_start + pre_slice_count;
    for (uint32_t pre_neuron_index = pre_slice_start;
            pre_neuron_index < pre_slice_end; pre_neuron_index++) {

        uint32_t max_n_synapses =
            max_row_n_synapses + max_delayed_row_n_synapses;
        uint16_t indices[max_n_synapses];
        uint32_t n_indices = connection_generator_generate(
            connection_generator, pre_slice_start, pre_slice_count,
            pre_neuron_index, post_slice_start, post_slice_count,
            max_n_synapses, indices);
        log_debug("Generated %u synapses", n_indices);

        // Generate delays for each index
        accum delay_params[n_indices];
        param_generator_generate(
            delay_generator, n_indices, pre_neuron_index, indices,
            delay_params);
        uint16_t delays[n_indices];
        for (uint32_t i = 0; i < n_indices; i++) {
            accum delay = delay_params[i] * timestep_per_delay;
            if (delay < 0) {
                delay = 1;
            }
            delays[i] = (uint16_t) delay;
            if (delay != delays[i]) {
                log_debug("Rounded delay %k to %u", delay, delays[i]);
            }

            struct delay_value delay_value = get_delay(delays[i], max_stage);
            if (delay_value.stage > 0) {
                bit_field_set(neuron_delay_stage_config[delay_value.stage - 1],
                    pre_neuron_index);
            }
        }
    }

    connection_generator_free(connection_generator);
    param_generator_free(delay_generator);

    return true;
}


bool read_sdram_data(
        address_t delay_params_address, address_t params_address) {

    uint32_t n_out_edges = delay_params_address[N_OUTGOING_EDGES];
    uint32_t num_neurons = delay_params_address[N_ATOMS];
    uint32_t neuron_bit_field_words = get_bit_field_size(num_neurons);
    uint32_t n_stages = delay_params_address[N_DELAY_STAGES];

    // Set up the bit fields
    bit_field_t *neuron_delay_stage_config = (bit_field_t*) spin1_malloc(
        n_stages * sizeof(bit_field_t));
    for (uint32_t d = 0; d < n_stages; d++) {
        neuron_delay_stage_config[d] = (bit_field_t)
            &(delay_params_address[DELAY_BLOCKS])
            + (d * neuron_bit_field_words);
        clear_bit_field(neuron_delay_stage_config[d], neuron_bit_field_words);
    }

    uint32_t pre_slice_start = *params_address++;
    uint32_t pre_slice_count = *params_address++;

    log_info("Generating %u delay edges for %u atoms starting at %u",
        n_out_edges, pre_slice_count, pre_slice_start);

    for (uint32_t edge = 0; edge < n_out_edges; edge++) {
        if (!read_delay_builder_region(
                &params_address, neuron_delay_stage_config,
                pre_slice_start, pre_slice_count)) {
            return false;
        }
    }

    return true;
}

void _start_expander(uint delay_params_address, uint params_address) {
    if (!read_sdram_data(
            (address_t) delay_params_address, (address_t) params_address)) {
        log_info("!!!   Error reading SDRAM data   !!!");
        rt_error(RTE_ABORT);
    }
    spin1_exit(0);
}

void c_main(void) {
    sark_cpu_state(CPU_STATE_RUN);

    // REGISTER_FACTORY_CLASS("KernelConnector", ConnectorGenerator, Kernel);
    // REGISTER_FACTORY_CLASS("MappingConnector", ConnectorGenerator, Mapping);
    // REGISTER_FACTORY_CLASS("FixedTotalNumberConnector", ConnectorGenerator, FixedTotalNumber);
    register_connection_generators();

    // REGISTER_FACTORY_CLASS("kernel",   ParamGenerator, ConvKernel);
    register_param_generators();

    log_debug("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));

    log_info("Starting To Build Connectors");

    address_t core_address = data_specification_get_data_address();
    address_t delay_params_address = data_specification_get_region(
        DELAY_PARAMS, core_address);
    address_t params_address = data_specification_get_region(
        EXPANDER_REGION, core_address);

    log_info("\tReading SDRAM delay params at 0x%08x,"
            " expander params at 0x%08x",
            delay_params_address, params_address);

    spin1_schedule_callback(
        _start_expander, (uint) delay_params_address, (uint) params_address, 1);

    spin1_start_paused();

    log_info("Finished On Machine Connectors!");
}
