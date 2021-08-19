#include "../../../../meanfield/plasticity/stdp/timing_dependence/my_timing_impl.h"

// TODO: Describe the layout of the configuration *in SDRAM*
typedef struct my_timing_config {
    accum my_potentiation_parameter;
    accum my_depression_parameter;
} my_timing_config_t;

// TODO: Set up any variables here
accum my_potentiation_parameter;
accum my_depression_parameter;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

    log_info("timing_initialise: starting");
    log_info("\tSTDP my timing rule");

    // TODO: copy parameters from memory
    my_timing_config_t *config = (my_timing_config_t *) address;
    my_potentiation_parameter = config->my_potentiation_parameter;
    my_depression_parameter = config->my_depression_parameter;

    log_info("my potentiation parameter = %k", my_potentiation_parameter);
    log_info("my depression parameter = %k", my_depression_parameter);
    log_info("timing_initialise: completed successfully");

    // Return the address after the configuration (word aligned)
    return (address_t) (config + 1);
}
