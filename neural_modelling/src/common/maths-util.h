/*

 maths-util.h -  first created 7/10/2013  version 0.1

 some defines and other helper types/functions for applying ACS/HR types and
 ideas to SpiNNaker numerical coding

 loose and transient toolbox of helper functions and macros until more
 structure present in maths libraries

 this version 4-2-2014 is slightly cut down to allow source builds of neuron
 update code

 */

#ifndef _MATHS_UTIL_
#define _MATHS_UTIL_

// disabled for production SpiNNaker builds but here for various testing
//#define FLOATING_POINT

// A Cardinal type
typedef unsigned int Card;

// just for my convenience with zero offset arrays
#define START 0

// this is where you switch between double precision (or float?) and
// fixed point accum (= signed 16.15)
#ifdef FLOATING_POINT

#include <math.h>

typedef double          REAL;
typedef double          UREAL;
typedef double          FRACT;
typedef double          UFRACT;
#define REAL_CONST(x)   x
#define UREAL_CONST(x)  x
#define FRACT_CONST(x)  x
#define UFRACT_CONST(x) x

static REAL macro_arg_1, macro_arg_2, macro_arg_3, macro_arg_4;

#define ONE             1.00000000000000000
#define HALF            0.50000000000000000
#define ZERO            0.00000000000000000

#define POW( x, p )     pow( (x), (p) )

#define SQRT( x )       sqrt( x )
#define EXP( x )        exp( x )
#define LN( x )         log( x )
#define ABS( x )        fabs(x)

//#define INV( x )       ONE/(x)

#define MAX( x, y )     MAX_HR(  (x), (y) )
#define SIGN( x, y )    ( (macro_arg_1=(y)) >= ZERO ? ABS( x ) : -ABS( x ) )

#define ACS_DBL_TINY    1.0e-300

#else   /* using fixed point types and functions */

#include <stdfix.h>
#include <stdfix-full-iso.h>

typedef accum                REAL;
typedef unsigned accum       UREAL;
typedef long fract           FRACT;
typedef unsigned long fract  UFRACT;
#define REAL_CONST(x)   x##k	 // accum -> k
#define UREAL_CONST(x)  x##uk    // unsigned accum -> uk
#define FRACT_CONST(x)  x##lr
#define UFRACT_CONST(x) x##ulr

#define ONE             REAL_CONST(1.0000)
#define HALF            REAL_CONST(0.5000)
#define ZERO            REAL_CONST(0.0000)
#define ACS_DBL_TINY    REAL_CONST(0.000001)

//#define SQRT( x )       sqrtfx( x )
//#define EXP( x )        expfx( x )
//#define LN( x )         lnfx( x )
//#define POW( x, p )     powfx( x, p )   // strictly positive x only

#define ABS( x )        absfx( x )

//#define INV( x )

//#define MAX( x, y )     maxfx( x, y )
#define SIGN( x, y )    ( (macro_arg_1=(y)) >= ZERO ? ABS( x ) : -ABS( x ) )

#endif

// some common operations that could be usefully speeded up
#ifdef FLOATING_POINT

#define REAL_COMPARE( x, op, y ) ( (x) op (y) )
#define REAL_TWICE( x ) ((x) * 2.00000 )
#define REAL_HALF( x )  ((x) * 0.50000 )

#else

#define REAL_COMPARE( x, op, y ) ( bitsk( (x) ) op  bitsk( (y) ) )
#define REAL_TWICE( x )  ((x) * 2.000000k ) // ((x) << 1 ) // // kbits( ( bitsk( (x) ) << 1 ) ) //((accum_dummy = (x)) * 2.000000k ) //  kbits( ( bitsk( (x) ) << 1 ) )  //* 2.000000k ) //((x) << 1)  //
#define REAL_HALF( x )   ((x) * 0.500000k ) // ((x) >> 1 ) // // kbits( ( bitsk( (x) ) >> 1 ) ) // ((accum_dummy = (x)) * 0.500000k ) //  kbits( ( bitsk( (x) ) >> 1 ) )   // ((x) * 0.500000k ) //((x) >> 1)

#endif

#define MIN_HR(a, b) ({\
    __type_of__(a) _a = (a); \
    __type_of__(b) _b = (b); \
    _a <= _b? _a : _b;})

#define MAX_HR(a, b) ({\
    __type_of__(a) _a = (a); \
    __type_of__(b) _b = (b); \
    _a > _b? _a : _b;})

#define SQR(a) ({\
    __type_of__(a) _a = (a); \
    _a == ZERO? ZERO: _a * _a;})

#define CUBE(a) ({\
    __type_of__(a) _a = (a); \
    _a == ZERO? ZERO: _a * _a * _a;})

#endif  // _MATHS_UTIL_

