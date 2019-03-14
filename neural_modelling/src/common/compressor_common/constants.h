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

//! enum for the different states to report through the user2 address.
typedef enum exit_states_for_user_one{
    EXITED_CLEANLY = 0, EXIT_FAIL = 1, EXIT_MALLOC = 2, EXIT_SWERR = 3
} exit_states_for_user_two;

#define __CONSTANTS_H__
#endif  // __CONSTANTS_H__