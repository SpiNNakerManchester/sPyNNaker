#ifndef _WEIGHT_ONE_TERM_H_
#define _WEIGHT_ONE_TERM_H_

#include "weight_interface.h"

static weight_state_t weight_one_term_apply_depression(weight_state_t state,
                                                int32_t depression);

static weight_state_t weight_one_term_apply_potentiation(weight_state_t state,
                                                  int32_t potentiation);

#endif // _WEIGHT_ONE_TERM_H_
