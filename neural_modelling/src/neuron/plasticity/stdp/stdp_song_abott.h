#ifndef _STDP_SONG_ABOTT_H_
#define _STDP_SONG_ABOTT_H_

// Include debug header for log_info etc
#include <debug.h>
#include <stdfix-exp.h>

// State stored per synapse
typedef struct {
    accum tlast_post;
    accum tlast_pre;
    accum delta_w;
    accum M;
    accum P;
    accum wsyn;
} plastic_synapse_t;

#include "stdp_rule.h"

// Global variables
static struct params {
    accum tauLTP;
    accum aLTP;
    accum tauLTD;
    accum aLTD;
    accum wmax;
    accum wmin;
} *params;

static inline void stdp_init(address_t address) {
    params = (struct params *) address;
}

static inline void stdp_on_presynaptic_spike(
        plastic_synapse_t *plastic_synapse, accum t) {
    plastic_synapse->P =
        plastic_synapse->P * expk((plastic_synapse->tlast_pre - t)
            / params->tauLTP)
        + params->aLTP;
    plastic_synapse->tlast_pre = t;
    plastic_synapse->delta_w =
        params->wmax * plastic_synapse->M *
        expk((plastic_synapse->tlast_post - t) / params->tauLTD);
    plastic_synapse->wsyn = plastic_synapse->wsyn + plastic_synapse->delta_w;
}

static inline void stdp_on_postsynaptic_spike(
        plastic_synapse_t *plastic_synapse, accum t) {
    plastic_synapse->M =
        plastic_synapse->M * expk((plastic_synapse->tlast_post - t)
            / params->tauLTD)
        - params->aLTD;
    plastic_synapse->tlast_post = t;
    plastic_synapse->delta_w =
        params->wmax * plastic_synapse->P *
        expk((plastic_synapse->tlast_pre - t) / params->tauLTP);
    plastic_synapse->wsyn = plastic_synapse->wsyn + plastic_synapse->delta_w;
}

static inline void stdp_do_boolean_checks(plastic_synapse_t *plastic_synapse) {
    if (plastic_synapse->wsyn > params->wmax) {
        plastic_synapse->wsyn = params->wmax;
    }
    if (plastic_synapse->wsyn < params->wmin) {
        plastic_synapse->wsyn = params->wmin;
    }
}

static inline accum stdp_get_weight(plastic_synapse_t *plastic_synapse) {
    return plastic_synapse->wsyn;
}

#endif // _STDP_SONG_ABOTT_H_
