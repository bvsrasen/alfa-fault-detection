CC ?= gcc
CFLAGS ?= -std=c99 -O2 -Wall -Wextra -Wpedantic -Wconversion -Wdouble-promotion -Werror
LDLIBS = -lm

build/alfa_cli: cli.c alfa_tespit.c alfa_param.c alfa_tespit.h | build
	$(CC) $(CFLAGS) -o $@ cli.c alfa_tespit.c alfa_param.c $(LDLIBS)

build:
	mkdir -p build

# Cortex-M4F (STM32F4) için kod boyutu; arm-none-eabi-gcc gerekiyor
ARM_CFLAGS = -std=c99 -Os -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -Wall -Wextra -Werror
arm: | build
	arm-none-eabi-gcc $(ARM_CFLAGS) -c alfa_tespit.c -o build/alfa_tespit_m4.o
	arm-none-eabi-gcc $(ARM_CFLAGS) -c alfa_param.c -o build/alfa_param_m4.o
	arm-none-eabi-size build/alfa_tespit_m4.o build/alfa_param_m4.o

clean:
	rm -rf build

.PHONY: arm clean
