#ifndef _MATHSBOX_H_
#define _MATHSBOX_H_

#include <sqrt.h>
#include <math.h>
#include <stdfix-exp.h>
//#include <common/math-utils.h>



struct mathsbox_t;

typedef struct mathsbox_t {

    REAL error_func_sample;
    
    REAL err_func;
}mathsbox_t;

//typedef struct mathsbox_params_t* mathsbox_pointer_t;

void error_function(REAL x, REAL factor, mathsbox_t *restrict mathsbox);
#endif