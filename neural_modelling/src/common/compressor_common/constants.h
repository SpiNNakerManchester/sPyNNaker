#ifndef __CONSTANTS_H__

//! max length of the router table entries
#define TARGET_LENGTH 1023

//! \brief timeout on attempts to send sdp message
#define _SDP_TIMEOUT 100

//! random port as 0 is in use by scamp/sark
#define RANDOM_PORT 4

//! word to byte multiplier
#define WORD_TO_BYTE_MULTIPLIER 4

//! flag for not requiring a reply
#define REPLY_NOT_EXPECTED 0x07

#define __CONSTANTS_H__
#endif  // __CONSTANTS_H__