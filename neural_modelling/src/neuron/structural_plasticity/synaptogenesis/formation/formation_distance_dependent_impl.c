#include "formation_distance_dependent_impl.h"

struct formation_params *synaptogenesis_formation_init(uint8_t **data) {
    // Reference the parameters to read the sizes
    struct formation_params *form_params = (struct formation_params *) *data;
    uint32_t data_size = sizeof(form_params) + sizeof(uint16_t) *
            (form_params->ff_prob_size + form_params->lat_prob_size);

    // Allocate the space for the data and copy it in
    form_params = (struct formation_params *) spin1_malloc(data_size);
    if (form_params == NULL) {
        log_error("Out of memory when allocating parameters");
        rt_error(RTE_SWERR);
    }
    spin1_memcpy(form_params, *data, data_size);
    *data += data_size;

    return form_params;
}
