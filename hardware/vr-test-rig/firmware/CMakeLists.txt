cmake_minimum_required(VERSION 3.13)
include(pico_sdk_import.cmake)

project(vr_rig_stepgen C CXX ASM)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()

add_executable(stepgen main.c)
pico_generate_pio_header(stepgen ${CMAKE_CURRENT_LIST_DIR}/stepgen.pio)
target_link_libraries(stepgen
    pico_stdlib
    pico_multicore
    hardware_pio
    hardware_clocks
)

# Commands arrive over USB CDC, not the UART pins.
pico_enable_stdio_usb(stepgen 1)
pico_enable_stdio_uart(stepgen 0)

pico_add_extra_outputs(stepgen)
