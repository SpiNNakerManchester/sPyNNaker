################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../spike_source/poisson/spike_source_poisson.c 

OBJS += \
./spike_source/poisson/spike_source_poisson.o 

C_DEPS += \
./spike_source/poisson/spike_source_poisson.d 


# Each subdirectory must supply rules for building sources it contributes
spike_source/poisson/%.o: ../spike_source/poisson/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -I"/Users/ghost/git/SpiNNMan/c_models" -I"/Users/ghost/git/spinnaker_tools/include" -I"/Users/ghost/git/SpiNNFrontEndCommon/c_common" -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


