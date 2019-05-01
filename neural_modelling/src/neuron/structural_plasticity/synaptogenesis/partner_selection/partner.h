#ifndef _PARTNER_SELECTION_H_
#define _PARTNER_SELECTION_H_

#include <neuron/synapses.h>

// MARS KISS 64 (RNG)
#include <random.h>
// Bit manipulation after RNG
#include <stdfix-full-iso.h>

#include <neuron/structural_plasticity/sp_structs.h>

// value to be returned when there is no valid partner selection
#define INVALID_SELECTION ((spike_t) - 1)

static inline bool potential_presynaptic_partner(
        rewiring_data_t *rewiring_data, uint32_t* population_id,
        uint32_t *sub_population_id, uint32_t *neuron_id, spike_t *spike);

#endif // _PARTNER_H_
