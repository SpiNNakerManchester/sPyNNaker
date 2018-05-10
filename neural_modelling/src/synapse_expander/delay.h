#include <stdint.h>

typedef struct delay {
    uint16_t source_neuron_id;
    uint16_t delay_stage;
} delay_t;


#define MAX_N_DELAYS_PER_PACKET 63
#define DELAY_SDP_PORT 1
#define DELAY_SDP_TAG 0
