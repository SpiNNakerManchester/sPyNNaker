#include "elimination_random_by_weight_impl.h"

struct elimination_params *synaptogenesis_elimination_init(uint8_t **data) {
    struct elimination_params *elim_params = (struct elimination_params *)
            spin1_malloc(sizeof(struct elimination_params));
    if (elim_params == NULL) {
        log_error("Out of memory when allocating parameters");
        rt_error(RTE_SWERR);
    }
    spin1_memcpy(elim_params, *data, sizeof(struct elimination_params));
    *data += sizeof(struct elimination_params);
    return elim_params;
}
