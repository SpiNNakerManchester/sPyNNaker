#ifndef _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_
#define _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_

#include "elimination.h"

static inline bool synaptogenesis_elimination_rule(rewiring_data_t *rewiring_data,
        current_state_t *current_state, uint32_t time, address_t row) {
    use(time);

    // Is synaptic weight <.5 g_max? (i.e. synapse is depressed)
    uint32_t r = mars_kiss64_seed(rewiring_data->local_seed);

    // get projection-specific weight from pop sub-population info table
    int appr_scaled_weight = rewiring_data->pre_pop_info_table
            .subpop_info[current_state->pop_index].weight;
    if (current_state->sp_data.weight < (appr_scaled_weight / 2) &&
            r > rewiring_data->p_elim_dep) {
        return false;
    }

    // otherwise, if synapse is potentiated, use probability 2
    if (current_state->sp_data.weight >= (appr_scaled_weight / 2) &&
            r > rewiring_data->p_elim_pot) {
        return false;
    }

    return sp_structs_remove_synapse(rewiring_data, current_state, row);
}

#endif // _ELIMINATION_RANDOM_BY_WEIGHT_IMPL_H_
