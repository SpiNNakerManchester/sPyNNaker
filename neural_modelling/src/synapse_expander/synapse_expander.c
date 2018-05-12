#include "synapse_expander.h"
#include "matrix_generator.h"
#include "connection_generator.h"
#include "param_generator.h"
#include "rng.h"
#include "delay_sender.h"

#include <stdbool.h>
#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>

//#define DEBUG_MESSAGES
#define SARK_HEAP 1

//----------------------------------------------------------------------------
// Module level variables
//----------------------------------------------------------------------------
#define SDRAM_TAG          140
#define MESSAGES_SDRAM_TAG 200
#define ID_DELAY_SDRAM_TAG 180
#define CLEAR_MEMORY_FLAG 0x55555555
#define SLEEP_TIME 10311

//TODO*** define this somewhere else!
#define BUILD_IN_MACHINE_PORT 1
#define BUILD_IN_MACHINE_TAG  111
#define MAX_N_DELAYS_PER_PACKET 100 // memory limits this
#define MAX_RETRIES 20
//TODO-END

#define _unused(x) ((void)(x))

matrix_generator_t matrix_generator;
connection_generator_t connection_generator;
param_generator_t weight_generator;
param_generator_t delay_generator;

bool delay_initialised = false;
uint32_t last_delay_chip = 0xFFFFFFFF;
uint32_t last_delay_core = 0xFFFFFFFF;

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

bool read_connection_builder_region(address_t *in_region,
        address_t synaptic_matrix_region, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t n_synapse_type_bits,
        uint32_t n_synapse_index_bits, int32_t *weight_scales) {

    uint32_t *region = *in_region;

    const uint32_t synaptic_matrix_offset = *region++;
    const uint32_t delayed_synaptic_matrix_offset = *region++;
    const uint32_t max_row_length = *region++;
    const uint32_t max_delayed_row_length = *region++;
    const uint32_t pre_slice_start = *region++;
    const uint32_t pre_slice_count = *region++;
    const uint32_t delay_chip = *region++;
    const uint32_t delay_core = *region++;
    const uint32_t max_stage = *region++;
    const uint32_t synapse_type = *region++;

    const uint32_t matrix_type_hash = *region++;
    const uint32_t connector_type_hash = *region++;
    const uint32_t weight_type_hash = *region++;
    const uint32_t delay_type_hash = *region++;

    // Set up to send delays
    if (delay_chip != 0xFFFFFFFF && delay_core != 0xFFFFFFFF) {
        if (delay_chip != last_delay_chip || delay_core != last_delay_core) {
            if (delay_initialised) {
                delay_sender_close();
            }
            delay_sender_initialize(delay_chip, delay_core);
            last_delay_chip = delay_chip;
            last_delay_core = delay_core;
            delay_initialised = true;
        }
    }

    // Generate matrix, connector, delays and weights
    matrix_generator = matrix_generator_init(matrix_type_hash, &region);
    connection_generator = connection_generator_init(connector_type_hash,
        &region);
    weight_generator = param_generator_init(weight_type_hash, &region);
    delay_generator = param_generator_init(delay_type_hash, &region);

    // Read RNG parameters for this matrix
    rng_t rng = rng_init(&region);

    *in_region = region;

    // If any components couldn't be created return false
    if (matrix_generator == NULL || connection_generator == NULL
            || delay_generator == NULL || weight_generator == NULL) {
        return false;
    }

    // Generate matrix
    address_t synaptic_matrix =
        &(synaptic_matrix_region[synaptic_matrix_offset]);
    address_t delayed_synaptic_matrix =
        &(synaptic_matrix_region[delayed_synaptic_matrix_offset]);
    bool status = matrix_generator_generate(
        matrix_generator, synaptic_matrix, delayed_synaptic_matrix,
        max_row_length, max_delayed_row_length,
        n_synapse_type_bits, n_synapse_index_bits,
        synapse_type, weight_scales,
        post_slice_start, post_slice_count,
        pre_slice_start, pre_slice_count,
        connection_generator, delay_generator, weight_generator,
        rng, max_stage);

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

    int32_t weight_scales[n_synapse_types];
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

void c_main(void) {
    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));
    sark_cpu_state(CPU_STATE_RUN);

    // Register matrix generators with factories
    // **NOTE** plastic matrix generator is capable of generating
    // both standard and extended plastic matrices
    // log_info("Matrix generators");
    // REGISTER_FACTORY_CLASS("StaticSynapticMatrix", MatrixGenerator, Static);
    // REGISTER_FACTORY_CLASS("PlasticSynapticMatrix", MatrixGenerator, Plastic);
    // REGISTER_FACTORY_CLASS("ExtendedPlasticSynapticMatrix", MatrixGenerator, Plastic);
    register_matrix_generators();

    // Register connector generators with factories
    // log_info("Connector generators");
    // REGISTER_FACTORY_CLASS("AllToAllConnector", ConnectorGenerator, AllToAll);
    // REGISTER_FACTORY_CLASS("OneToOneConnector", ConnectorGenerator, OneToOne);
    // REGISTER_FACTORY_CLASS("FixedProbabilityConnector", ConnectorGenerator, FixedProbability);
    // REGISTER_FACTORY_CLASS("KernelConnector", ConnectorGenerator, Kernel);
    // REGISTER_FACTORY_CLASS("MappingConnector", ConnectorGenerator, Mapping);
    // REGISTER_FACTORY_CLASS("FixedTotalNumberConnector", ConnectorGenerator, FixedTotalNumber);
    register_connection_generators();

    // Register parameter generators with factories
    // log_info("Parameter generators");
    // REGISTER_FACTORY_CLASS("constant", ParamGenerator, Constant);
    // REGISTER_FACTORY_CLASS("kernel",   ParamGenerator, ConvKernel);
    // REGISTER_FACTORY_CLASS("uniform",  ParamGenerator, Uniform);
    // REGISTER_FACTORY_CLASS("normal",   ParamGenerator, Normal);
    //  REGISTER_FACTORY_CLASS("normal_clipped", ParamGenerator, NormalClipped);
    //  REGISTER_FACTORY_CLASS("normal_clipped_to_boundary", ParamGenerator, NormalClippedToBoundary);
    // REGISTER_FACTORY_CLASS("exponential", ParamGenerator, Exponential);
    register_param_generators();

    // Allocate buffers for placement new from factories
    // **NOTE** we need to be able to simultaneously allocate a delay and
    // a weight generator so we need two buffers for parameter allocation
    // g_MatrixGeneratorBuffer = g_MatrixGeneratorFactory.Allocate();
    // g_ConnectorGeneratorBuffer = g_ConnectorGeneratorFactory.Allocate();
    // g_DelayParamGeneratorBuffer = g_ParamGeneratorFactory.Allocate();
    // g_WeightParamGeneratorBuffer = g_ParamGeneratorFactory.Allocate();

    // Get this core's base address using alloc tag
    // uint32_t *params_address = Config::GetBaseAddressAllocTag();
    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));

    log_info("Starting To Build Connectors");
    // If reading SDRAM data fails

    address_t core_address = data_specification_get_data_address();
    address_t params_address = data_specification_get_region(
        CONNECTOR_BUILDER_REGION, core_address);
    address_t syn_mtx_addr = data_specification_get_region(
        SYNAPTIC_MATRIX_REGION, core_address);

    log_info("\tReading SDRAM at 0x%08x", params_address);

    if (!read_sdram_data(params_address, syn_mtx_addr)) {
        log_info("!!!   Error reading SDRAM data   !!!");
        rt_error(RTE_ABORT);
    }

    if (delay_initialised) {
        delay_sender_close();
    }

    log_info("Finished On Machine Connectors!");
}
