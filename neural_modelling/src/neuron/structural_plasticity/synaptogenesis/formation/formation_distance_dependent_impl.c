#include "formation_distance_dependent_impl.h"

form_dist_params *form_dd_params;
uint16_t *ff_probs;
uint16_t *lat_probs;

address_t synaptogenesis_formation_init(address_t data) {
    // Reference the parameters to read the sizes
    form_dd_params = (form_dist_params *) data;
    uint32_t data_size = sizeof(form_dist_params) + sizeof(uint16_t) *
            (form_dd_params->ff_prob_size + form_dd_params->lat_prob_size);

    // Allocate the space for the data and copy it in
    form_dd_params = (form_dist_params *) spin1_malloc(data_size);
    if (form_dd_params == NULL) {
        log_error("Out of memory when allocating parameters");
        rt_error(RTE_SWERR);
    }
    spin1_memcpy(form_dd_params, data, data_size);

    // Put the pointers into place
    ff_probs = &form_dd_params->prob_tables[0];
    lat_probs = &form_dd_params->prob_tables[form_dd_params->ff_prob_size];

    // Return beyond the data
    return ((uint8_t *) data) + data_size;
}
