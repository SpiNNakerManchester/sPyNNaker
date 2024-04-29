/*
 * Copyright (c) 2013 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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

extern uint64_t udiv64(uint64_t, uint64_t);

//! \brief Divides an accum by another accum
//! \param[in] a The dividend
//! \param[in] b The divisor
//! \return a divided by b
static inline REAL kdivk(REAL a, REAL b) {
	return kbits((uint32_t) udiv64(((uint64_t) bitsk(a) << 15), (uint64_t) bitsk(b)));
}

//! \brief Divides an unsigned accum by another unsigned accum
//! \param[in] a The dividend
//! \param[in] b The divisor
//! \return a divided by b
static inline UREAL ukdivuk(UREAL a, UREAL b) {
	return ukbits((uint32_t) udiv64(((uint64_t) bitsuk(a) << 16), (uint64_t) bitsuk(b)));
}

//! \brief Divides an integer by an accum
//! \param[in] a The dividend
//! \param[in] b The divisor
//! \return a divided by b
static inline int32_t udivk(int32_t a, REAL b) {
    return __LI(udiv64(__U64(a) << 15, __U64(bitsk(b))));
}

//! \brief Divides an accum by an unsigned integer
//! \param[in] a The dividend
//! \param[in] b The divisor
//! \return a divided by b
static inline REAL kdivui(REAL a, uint32_t b) {
	return kbits((uint32_t) __LI(udiv64(__U64(bitsk(a)), __U64(b))));
}

//! 2^(1/(2^n)) for values of n between 1 and 15, in U1616 format, then converted
//! to uint32_t for computation.
//! These can be used to work out fractional powers of 2 by multiplication.
static const uint32_t fract_powers_2[] = {
	0x16a09, 0x1306f, 0x1172b, 0x10b55, 0x1059b, 0x102c9, 0x10163, 0x100b1,
	0x10058, 0x1002c, 0x10016, 0x1000b, 0x10005, 0x10002, 0x10001
};


//! 2^-(1/2^n)) for values of n between 1 and 15, in U1616 format, then converted
//! to uint32_t for computation.
//! These can be used to work out negative fractional power of 2 by multiplication.
static const uint32_t fract_powers_half[] = {
	0xb504, 0xd744, 0xeac0, 0xf525, 0xfa83, 0xfd3e, 0xfe9e, 0xff4e, 0xffa7,
	0xffd3, 0xffe9, 0xfff4, 0xfffa, 0xfffd, 0xfffe
};

//! \brief Calculates 2^p where p is a real number (rather than just an integer).
//!        This is still quicker than general power operations.
//! \param[in] p The power to raise 2 to; if p >= 16 or <= -16 the result will
//!              be saturated to MAX_U_REAL or 0 respectively.
static inline UREAL pow_of_2(REAL p) {

	// The variable that will hold the return value
	uint32_t accumulator;

	// The fractional bits from the input
	uint32_t fract_bits;

	// The powers to use in the calculation
	const uint32_t *powers;

	if (p >= 0) {
		if (p >= 16) {
			return kbits(0xFFFFFFFF);
		}
		accumulator = bitsuk(UREAL_CONST(1)) << (bitsk(p) >> 15);
		fract_bits = bitsk(p) & 0x7FFF;
		powers = fract_powers_2;
	} else {
		if (p <= -16) {
			return kbits(0);
		}
		REAL val = p * REAL_CONST(-1);
		accumulator = bitsuk(UREAL_CONST(1)) >> (bitsk(val) >> 15);
		fract_bits = bitsk(val) & 0x7FFF;
		powers = fract_powers_half;
	}

	// Multiply in fractional powers for each non-zero fractional bits
	for (uint32_t i = 0; i < 15; i++) {
		uint32_t bit = (fract_bits >> (14 - i)) & 0x1;
		if (bit) {
			uint32_t f = bit * powers[i];
			accumulator = __stdfix_smul_uk(accumulator, f);
		}
	}

	return ukbits(accumulator);
}

#endif  // _MATHS_UTIL_
