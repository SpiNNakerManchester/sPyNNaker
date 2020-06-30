/*
 * Copyright (c) 2013-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

/**

\file

\brief maths-util.h -  first created 7/10/2013  version 0.1

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

//! A Cardinal type
typedef unsigned int	Card;

//! just for my convenience with zero offset arrays
#define START		0

// this is where you switch between double precision (or float?) and
// fixed point accum (= signed 16.15)
#ifdef FLOATING_POINT

#include <math.h>

typedef double		REAL;
typedef double		UREAL;
typedef double		FRACT;
typedef double		UFRACT;
#define REAL_CONST(x)	x
#define UREAL_CONST(x)	x
#define FRACT_CONST(x)	x
#define UFRACT_CONST(x)	x

static REAL macro_arg_1, macro_arg_2, macro_arg_3, macro_arg_4;

#define ONE		1.00000000000000000
#define HALF		0.50000000000000000
#define ZERO		0.00000000000000000

#define POW(x, p)	pow((x), (p))

#define SQRT(x)		sqrt(x)
#define EXP(x)		exp(x)
#define LN(x)		log(x)
#define ABS(x)		fabs(x)

//#define INV(x)	ONE/(x)

#define MAX(x, y)	MAX_HR((x), (y))
#define SIGN(x, y)	((macro_arg_1=(y)) >= ZERO ? ABS(x) : -ABS(x))

#define ACS_DBL_TINY    1.0e-300

#else   /* using fixed point types and functions */

#include <stdfix.h>
#include <stdfix-full-iso.h>
#include <stdfix-exp.h>
#include <sqrt.h>

//! Type used for "real" numbers
typedef accum			REAL;

//! Type used for "unsigned real" numbers
typedef unsigned accum	UREAL;

//! Type used for "fractional" numbers
typedef long fract		FRACT;

//! Type used for "unsigned fractional" numbers
typedef unsigned long fract	UFRACT;

//! \brief Define a constant of type ::REAL
//! \param x The _literal form_ of the number
#define REAL_CONST(x)	x##k		// accum -> k

//! \brief Define a constant of type ::UREAL
//! \param x The _literal form_ of the number
#define UREAL_CONST(x)	x##uk		// unsigned accum -> uk

//! \brief Define a constant of type ::FRACT
//! \param x The _literal form_ of the number
#define FRACT_CONST(x)	x##lr

//! \brief Define a constant of type ::UFRACT
//! \param x The _literal form_ of the number
#define UFRACT_CONST(x)	x##ulr

//! A ::REAL 1.0
#define ONE 		REAL_CONST(1.0000)
//! A ::REAL 0.5
#define HALF		REAL_CONST(0.5000)
//! A ::REAL 0.0
#define ZERO		REAL_CONST(0.0000)
//! A ::REAL "very small number" (0.000001)
#define ACS_DBL_TINY	REAL_CONST(0.000001)

//! \brief This calculates the square-root of the argument
//! \param[in] x: The ::REAL-valued argument
//! \return The ::REAL-valued square root of the argument
#define SQRT(x)	    sqrtk(x)

//! \brief This calculates the exponential (to base _e_) of the argument
//! \param[in] x: The ::REAL-valued argument
//! \return The ::REAL-valued exponential of the argument
#define EXP(x)		expk(x)

#if 0
//! \brief This calculates the logarithm (to base _e_) of the argument
//! \param[in] x: The ::REAL-valued argument
//! \return The ::REAL-valued log of the argument
#define LN(x)		lnfx(x)

//! \brief This calculates the power of one argument to another
//! \param[in] x: The ::REAL-valued argument (must be _strictly positive_)
//! \param[in] x: The ::REAL-valued power
//! \return The ::REAL power
#define POW(x, p)	powfx(x, p)   // strictly positive x only
#endif

//! \brief This calculates the absolute value of the argument
//! \param[in] x: The ::REAL-valued argument
//! \return The ::REAL-valued absolute value of the argument
#define ABS(x)		absfx(x)

//#define INV(x)

//#define MAX(x, y)	maxfx(x, y)

//! \brief This calculates the value of an argument with the sign copied from
//!     another argument.
//! \param[in] x: The ::REAL value to take the absolute value from
//! \param[in] y: The ::REAL value to take the sign from.
//! \return ::REAL value that is the combination of the two
#define SIGN(x, y)	((macro_arg_1=(y)) >= ZERO ? ABS(x) : -ABS(x))

#endif // FLOATING_POINT

// some common operations that could be usefully speeded up
#ifdef FLOATING_POINT

#define REAL_COMPARE(x, op, y)	((x) op (y))
#define REAL_TWICE(x)	((x) * 2.00000)
#define REAL_HALF(x)	((x) * 0.50000)

#else // !FLOATING_POINT

//! \brief Compare two ::REAL numbers
//! \param[in] x: The first ::REAL value to compare
//! \param op: The comparison operator (e.g., `>=`)
//! \param[in] y: The second ::REAL value to compare
//! \return True if the comparison returns true, false otherwise
#define REAL_COMPARE(x, op, y)	(bitsk((x)) op bitsk((y)))

//! \brief Multiply by two
//! \param[in] x: The ::REAL argument
//! \return The ::REAL value that is twice the value of the argument
#define REAL_TWICE(x)	((x) * 2.000000k)

//! \brief Divide by two
//! \param[in] x: The ::REAL argument
//! \return The ::REAL value that is half the value of the argument
#define REAL_HALF(x)	((x) * 0.500000k)

#endif // FLOATING_POINT

//! Minimum of two values
#define MIN_HR(a, b) ({\
    __type_of__(a) _a = (a); \
    __type_of__(b) _b = (b); \
    _a <= _b? _a : _b;})

//! Maximum of two values
#define MAX_HR(a, b) ({\
    __type_of__(a) _a = (a); \
    __type_of__(b) _b = (b); \
    _a > _b? _a : _b;})

//! Square of a value
#define SQR(a) ({\
    __type_of__(a) _a = (a); \
    _a == ZERO? ZERO: _a * _a;})

//! Cube of a value
#define CUBE(a) ({\
    __type_of__(a) _a = (a); \
    _a == ZERO? ZERO: _a * _a * _a;})

#endif  // _MATHS_UTIL_
