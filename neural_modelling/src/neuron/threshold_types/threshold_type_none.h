#ifndef _THRESHOLD_TYPE_NONE_H_
#define _THRESHOLD_TYPE_NONE_H_

#include "threshold_type.h"

typedef struct threshold_type_t {
} threshold_type_t;

static inline bool threshold_type_is_above_threshold(state_t value,
                        threshold_type_pointer_t threshold_type) {
	use(value);
	use(threshold_type);
    return 0;
}

#endif // _THRESHOLD_TYPE_NONE_H_
