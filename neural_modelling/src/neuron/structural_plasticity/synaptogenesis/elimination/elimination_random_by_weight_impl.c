#include "elimination_random_by_weight_impl.h"

elimination_params *elim_params;

address_t synaptogenesis_elimination_init(address_t data) {
    elim_params = (elimination_params *) spin1_malloc(
        sizeof(elimination_params));
    if (elim_params == NULL) {
        log_error("Out of memory when allocating parameters");
        rt_error(RTE_SWERR);
    }
    spin1_memcpy(form_params, data, sizeof(elimination_params));

    return ((uint8_t *) data) + sizeof(elimination_params);
}
