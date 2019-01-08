#ifndef _PARTNER_SELECTION_H_
#define _PARTNER_SELECTION_H_

#include <neuron/synapses.h>

// MARS KISS 64 (RNG)
#include <random.h>
// Bit manipulation after RNG
#include <stdfix-full-iso.h>

static spike_t potential_presynaptic_partner(mars_kiss64_seed_t seed);

#endif // _PARTNER_H_