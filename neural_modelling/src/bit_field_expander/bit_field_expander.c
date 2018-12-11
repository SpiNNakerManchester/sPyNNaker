

#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>

address_t row_address;

bool initialise_master_pop_tables(){
    if (!population_table_initialise(
            data_specification_get_region(POPULATION_TABLE_REGION, address),
            indirect_synapses_address, direct_synapses_address,
            &row_max_n_words)) {
        return false;
    }
}


void c_main(void) {
    sark_cpu_state(CPU_STATE_RUN);

    log_info("starting the bit field expander");

    read_in_addresses();

    initialise_master_pop_table();



    // Register each of the components
    register_matrix_generators();
    register_connection_generators();
    register_param_generators();

    // Get the addresses of the regions
    log_info("Starting To Build bit fields");
    address_t core_address = data_specification_get_data_address();
    address_t params_address = data_specification_get_region(
        CONNECTOR_BUILDER_REGION, core_address);
    address_t syn_mtx_addr = data_specification_get_region(
        SYNAPTIC_MATRIX_REGION, core_address);
    log_info("\tReading SDRAM at 0x%08x, writing to matrix at 0x%08x",
            params_address, syn_mtx_addr);

    // Run the expander
    if (!read_sdram_data(
            (address_t) params_address, (address_t) syn_mtx_addr)) {
        log_info("!!!   Error reading SDRAM data   !!!");
        rt_error(RTE_ABORT);
    }

    log_info("Finished On Machine Connectors!");
}
