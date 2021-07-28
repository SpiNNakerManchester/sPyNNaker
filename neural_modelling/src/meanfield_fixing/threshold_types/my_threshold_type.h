#ifndef _MY_THRESHOLD_TYPE_H_
#define _MY_THRESHOLD_TYPE_H_

#include <neuron/threshold_types/threshold_type.h>

typedef struct threshold_type_t {
    // TODO: Add any additional parameters here
    REAL threshold_value;
    REAL my_param;
} threshold_type_t;

static inline bool threshold_type_is_above_threshold(state_t value,
        threshold_type_t *threshold_type) {

    // TODO: Perform the appropriate operations
    REAL test_value = value * threshold_type->my_param;

    // TODO: Update to return true or false depending on if the
    // threshold has been reached
    return REAL_COMPARE(test_value, >=, threshold_type->threshold_value);
}

#endif // _MY_THRESHOLD_TYPE_H_
