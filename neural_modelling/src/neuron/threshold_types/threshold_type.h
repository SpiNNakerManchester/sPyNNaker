#ifndef _THRESHOLD_TYPE_H_
#define _THRESHOLD_TYPE_H_

#include "../../common/neuron-typedefs.h"

//! Forward declaration of the threshold pointer type
typedef struct threshold_type_t* threshold_type_pointer_t;

//! \brief Determines if the value given is above the threshold value
//! \param[in] value The value to determine if it is above the threshold
//! \param[in] params The parameters to use to determine the result
static bool threshold_type_is_above_threshold(
    state_t value, threshold_type_pointer_t threshold_type);

#endif // _THRESHOLD_TYPE_H_
