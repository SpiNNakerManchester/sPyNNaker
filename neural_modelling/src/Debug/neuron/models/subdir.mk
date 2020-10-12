################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../neuron/models/neuron_model_izh_impl.c \
../neuron/models/neuron_model_lif_impl.c 

OBJS += \
./neuron/models/neuron_model_izh_impl.o \
./neuron/models/neuron_model_lif_impl.o 

C_DEPS += \
./neuron/models/neuron_model_izh_impl.d \
./neuron/models/neuron_model_lif_impl.d 


# Each subdirectory must supply rules for building sources it contributes
neuron/models/%.o: ../neuron/models/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -I"/Users/ghost/git/SpiNNMan/c_models" -I"/Users/ghost/git/spinnaker_tools/include" -I"/Users/ghost/git/SpiNNFrontEndCommon/c_common" -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


