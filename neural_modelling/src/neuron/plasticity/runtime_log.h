#ifndef RUNTIME_LOG
#define RUNTIME_LOG

#include <debug.h>

//---------------------------------------
// Externals
//---------------------------------------
#ifdef DEBUG
extern bool plastic_runtime_log_enabled;

#define plastic_runtime_log_info(i, ...)  \
  do { if(plastic_runtime_log_enabled) { log_info(i, ##__VA_ARGS__); }} while(0)

#else

#define plastic_runtime_log_info(i, ...) skip()

#endif	// DEBUG

#endif  // RUNTIME_LOG
