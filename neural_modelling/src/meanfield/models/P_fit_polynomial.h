#ifndef _P_FIT_POLYNOMIAL_H_
#define _P_FIT_POLYNOMIAL_H_

#include "../../meanfield/models/meanfield_model.h"

typedef struct pFitPolynomial_t {
    // nominally 'fixed' parameters
/*! \brief a structure for the polynomial parameters coming from a single neuron fit
 *  MORE INFO 
*/
    REAL P0;
    REAL P1;
    REAL P2;
    REAL P3;
    REAL P4;
    REAL P5;
    REAL P6;
    REAL P7;
    REAL P8;
    REAL P9;
    REAL P10;
} pFitPolynomial_t;


#endif