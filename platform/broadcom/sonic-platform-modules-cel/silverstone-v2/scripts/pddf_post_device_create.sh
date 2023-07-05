#!/bin/bash
# install custom fpga device.

sleep 3
modprobe pddf_custom_fpga_extend
# init SAT LED
i2cset -y -f 100 0x0d 0x01
