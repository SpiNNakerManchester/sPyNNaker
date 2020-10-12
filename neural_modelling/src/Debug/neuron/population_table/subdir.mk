################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../neuron/population_table/population_table_binary_search_impl.c \
../neuron/population_table/population_table_fixed_impl.c 

OBJS += \
./neuron/population_table/population_table_binary_search_impl.o \
./neuron/population_table/population_table_fixed_impl.o 

C_DEPS += \
./neuron/population_table/population_table_binary_search_impl.d \
./neuron/population_table/population_table_fixed_impl.d 


# Each subdirectory must supply rules for building sources it contributes
neuron/population_table/%.o: ../neuron/population_table/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -I"/Users/ghost/git/SpiNNMan/c_models" -I"/Users/ghost/git/spinnaker_tools/include" -I"/Users/ghost/git/SpiNNFrontEndCommon/c_common" -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


