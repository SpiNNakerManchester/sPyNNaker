#ifndef _INPUT_TYPE_H_
#define _INPUT_TYPE_H_

#ifndef INPUT_TYPE_CLASS
#   error "Must define INPUT_TYPE_CLASS to use this header"
#else // INPUT_TYPE_CLASS defined
#   define INPUT_TYPE_CLASS_Current 0
#   define INPUT_TYPE_CLASS_Conductance 1
#   define INPUT_TYPE_CLASS_CODE INPUT_TYPE_CLASS_##INPUT_TYPE_CLASS
#   if INPUT_TYPE_CLASS_CODE == INPUT_TYPE_CLASS_Current
#       include "input_type_current.h"
#   elif INPUT_TYPE_CLASS_CODE == INPUT_TYPE_CLASS_Conductance
#       include "input_type_conductance.h"
#   endif // INPUT_TYPE_CLASS_CODE
#endif // INPUT_TYPE_CLASS

#endif // _INPUT_TYPE_H_
