#ifndef _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_
#define _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_

#include "elimination.h"

struct elimination_params {
    uint32_t prob_elim_depression;
    uint32_t prob_elim_potentiation;
    int32_t mid_weight;
};

static inline bool synaptogenesis_elimination_rule(
        current_state_t *current_state, struct elimination_params* params,
        uint32_t time, address_t row) {
    use(time);

    // Is synaptic weight <.5 g_max? (i.e. synapse is depressed)
    uint32_t r = mars_kiss64_seed(*(current_state->local_seed));

    // Is weight depressed?
    if (current_state->weight < params->mid_weight &&
            r > params->prob_elim_depression) {
        return false;
    }

    // Is weight potentiated or unchanged?
    if (current_state->weight >= params->mid_weight &&
            r > params->prob_elim_potentiation) {
        return false;
    }

    return sp_structs_remove_synapse(current_state, row);
}

#endif // _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_
