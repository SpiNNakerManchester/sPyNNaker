#ifndef _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_
#define _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_

#include "elimination.h"

typedef struct elimination_params {
    uint32_t prob_elim_depression;
    uint32_t prob_elim_potentiation;
    int32_t mid_weight;
} elimination_params;

extern elimination_params *elim_params;

static inline bool synaptogenesis_elimination_rule(
        rewiring_data_t *rewiring_data, current_state_t *current_state,
        uint32_t time, address_t row) {
    use(time);

    // Is synaptic weight <.5 g_max? (i.e. synapse is depressed)
    uint32_t r = mars_kiss64_seed(rewiring_data->local_seed);

    // Is weight depressed?
    if (current_state->sp_data.weight < elim_params->mid_weight &&
            r > elim_params->prob_elim_depression) {
        return false;
    }

    // Is weight potentiated or unchanged?
    if (current_state->sp_data.weight >= elim_params->mid_weight &&
            r > elim_params->prob_elim_potentiation) {
        return false;
    }

    return sp_structs_remove_synapse(rewiring_data, current_state, row);
}

#endif // _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_
