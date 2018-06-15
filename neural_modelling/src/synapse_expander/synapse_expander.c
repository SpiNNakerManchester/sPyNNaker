#include "synapse_expander.h"
#include "matrix_generator.h"
#include "connection_generator.h"
#include "param_generator.h"

#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>

#define _unused(x) ((void)(x))

bool read_connection_builder_region(address_t *in_region,
        address_t synaptic_matrix_region, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t n_synapse_type_bits,
        uint32_t n_synapse_index_bits, uint32_t *weight_scales) {

    address_t region = *in_region;

    const uint32_t synaptic_matrix_offset = *region++;
    const uint32_t delayed_synaptic_matrix_offset = *region++;
    const uint32_t max_row_n_words = *region++;
    const uint32_t max_delayed_row_n_words = *region++;
    const uint32_t max_row_n_synapses = *region++;
    const uint32_t max_delayed_row_n_synapses = *region++;
    const uint32_t pre_slice_start = *region++;
    const uint32_t pre_slice_count = *region++;
    const uint32_t max_stage = *region++;
    accum timestep_per_delay;
    spin1_memcpy(&timestep_per_delay, region++, sizeof(accum));
    const uint32_t synapse_type = *region++;

    const uint32_t matrix_type_hash = *region++;
    const uint32_t connector_type_hash = *region++;
    const uint32_t weight_type_hash = *region++;
    const uint32_t delay_type_hash = *region++;

    // Generate matrix, connector, delays and weights
    matrix_generator_t matrix_generator =
        matrix_generator_init(matrix_type_hash, &region);
    connection_generator_t connection_generator =
        connection_generator_init(connector_type_hash, &region);
    param_generator_t weight_generator =
        param_generator_init(weight_type_hash, &region);
    param_generator_t delay_generator =
        param_generator_init(delay_type_hash, &region);

    *in_region = region;

    // If any components couldn't be created return false
    if (matrix_generator == NULL || connection_generator == NULL
            || delay_generator == NULL || weight_generator == NULL) {
        return false;
    }

    log_debug("Synaptic matrix offset = %u, delayed offset = %u",
            synaptic_matrix_offset, delayed_synaptic_matrix_offset);
    log_debug("Max row synapses = %u, max delayed row synapses = %u",
            max_row_n_synapses, max_delayed_row_n_synapses);

    // Generate matrix
    address_t synaptic_matrix = NULL;
    if (synaptic_matrix_offset != 0xFFFFFFFF) {
        synaptic_matrix = &(synaptic_matrix_region[synaptic_matrix_offset]);
    }
    address_t delayed_synaptic_matrix = NULL;
    if (delayed_synaptic_matrix_offset != 0xFFFFFFFF) {
        delayed_synaptic_matrix =
            &(synaptic_matrix_region[delayed_synaptic_matrix_offset]);
    }
    log_debug("Generating matrix at 0x%08x, delayed at 0x%08x",
            synaptic_matrix, delayed_synaptic_matrix);
    bool status = matrix_generator_generate(
        matrix_generator, synaptic_matrix, delayed_synaptic_matrix,
        max_row_n_words, max_delayed_row_n_words,
        max_row_n_synapses, max_delayed_row_n_synapses,
        n_synapse_type_bits, n_synapse_index_bits,
        synapse_type, weight_scales,
        post_slice_start, post_slice_count,
        pre_slice_start, pre_slice_count,
        connection_generator, delay_generator, weight_generator,
        max_stage, timestep_per_delay);

    matrix_generator_free(matrix_generator);
    connection_generator_free(connection_generator);
    param_generator_free(weight_generator);
    param_generator_free(delay_generator);

    if (!status) {
        log_error("\tMatrix generation failed");
        return false;
    }

    return true;
}


bool read_sdram_data(
        address_t params_address, address_t synaptic_matrix_region) {

    uint32_t n_in_edges = *params_address++;

    uint32_t post_slice_start = *params_address++;
    uint32_t post_slice_count = *params_address++;

    uint32_t n_synapse_types = *params_address++;
    uint32_t n_synapse_type_bits = *params_address++;
    uint32_t n_synapse_index_bits = *params_address++;

    log_info("Generating %u edges for %u atoms starting at %u",
        n_in_edges, post_slice_count, post_slice_start);

    uint32_t weight_scales[n_synapse_types];
    for (uint32_t i = 0; i < n_synapse_types; i++) {
        weight_scales[i] = *params_address++;
    }

    for (uint32_t edge = 0; edge < n_in_edges; edge++) {
        if (!read_connection_builder_region(
                &params_address, synaptic_matrix_region,
                post_slice_start, post_slice_count, n_synapse_type_bits,
                n_synapse_index_bits, weight_scales)) {
            return false;
        }
    }

    return true;
}

void _start_expander(uint params_address, uint syn_mtx_addr) {
    if (!read_sdram_data(
            (address_t) params_address, (address_t) syn_mtx_addr)) {
        log_info("!!!   Error reading SDRAM data   !!!");
        rt_error(RTE_ABORT);
    }
    spin1_exit(0);
}

void c_main(void) {
    sark_cpu_state(CPU_STATE_RUN);

    register_matrix_generators();

    // REGISTER_FACTORY_CLASS("KernelConnector", ConnectorGenerator, Kernel);
    // REGISTER_FACTORY_CLASS("MappingConnector", ConnectorGenerator, Mapping);
    // REGISTER_FACTORY_CLASS("FixedTotalNumberConnector", ConnectorGenerator, FixedTotalNumber);
    register_connection_generators();

    // REGISTER_FACTORY_CLASS("kernel",   ParamGenerator, ConvKernel);
    register_param_generators();

    log_debug("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));

    log_info("Starting To Build Connectors");

    address_t core_address = data_specification_get_data_address();
    address_t params_address = data_specification_get_region(
        CONNECTOR_BUILDER_REGION, core_address);
    address_t syn_mtx_addr = data_specification_get_region(
        SYNAPTIC_MATRIX_REGION, core_address);

    log_info("\tReading SDRAM at 0x%08x, writing to matrix at 0x%08x",
            params_address, syn_mtx_addr);

    spin1_schedule_callback(
        _start_expander, (uint) params_address, (uint) syn_mtx_addr, 1);

    spin1_start_paused();

    log_info("Finished On Machine Connectors!");
}
