#ifndef _WEIGHT_TWO_TERM_H_
#define _WEIGHT_TWO_TERM_H_

#include "weight.h"

static weight_state_t weight_two_term_apply_depression(weight_state_t state,
                                                int32_t depression_1,
                                                int32_t depression_2);

static weight_state_t weight_two_term_apply_potentiation(weight_state_t state,
                                                  int32_t potentiation_1,
                                                  int32_t potentiation_2);

#endif // _WEIGHT_TWO_TERM_H_
