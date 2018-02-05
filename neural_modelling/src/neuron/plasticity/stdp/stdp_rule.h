static inline void stdp_init(address_t params_address);

static inline void stdp_on_presynaptic_spike(
        plastic_synapse_t *plastic_synapse, accum t);

static inline void stdp_on_postsynaptic_spike(
        plastic_synapse_t *plastic_synapse, accum t);

static inline void stdp_do_boolean_checks(
        plastic_synapse_t *plastic_synapse);

static inline accum stdp_get_weight(
        plastic_synapse_t *plastic_synapse);
