#include <stdint.h>

//! \brief Prepares to send delays to the given chip and core
//! \param[in] delay_chip The x and y coordinate of the chip to send delays to
//! \param[in] delay_core The core on delay chip to send delays to
void delay_sender_initialize(uint32_t delay_chip, uint32_t delay_core);

//! \brief Flush any delays that have been queued for sending
void delay_sender_flush();

//! \brief Add a delay to be sent, possibly flushing if enough are ready
//! \param[in] index The index of the source neuron to be delayed
//! \param[in] stage The number of delay stages to pass through
void delay_sender_send(uint32_t index, uint32_t stage);

//! \brief Finish sending all delays and tell the delay core you are done
void delay_sender_close();
