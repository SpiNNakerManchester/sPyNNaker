################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../neuron/c_main.c \
../neuron/neuron.c \
../neuron/spike_processing.c \
../neuron/synapses.c 

OBJS += \
./neuron/c_main.o \
./neuron/neuron.o \
./neuron/spike_processing.o \
./neuron/synapses.o 

C_DEPS += \
./neuron/c_main.d \
./neuron/neuron.d \
./neuron/spike_processing.d \
./neuron/synapses.d 


# Each subdirectory must supply rules for building sources it contributes
neuron/%.o: ../neuron/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -I"/Users/ghost/git/SpiNNMan/c_models" -I"/Users/ghost/git/spinnaker_tools/include" -I"/Users/ghost/git/SpiNNFrontEndCommon/c_common" -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


