#!/bin/bash

# Platform init script

NUM_I2C_1_DEVICE=1

# MAIN MUX PCA9548 0x71
NUM_MUX_9548_CH0=$(( ${NUM_I2C_DEVICE} + 1 )) # MUX #1 SFP28 Port1 EEPROM 0x50
NUM_MUX_9548_CH1=$(( ${NUM_I2C_DEVICE} + 2 )) # MUX #2 SFP28 Port2 EEPROM 0x50
NUM_MUX_9548_CH2=$(( ${NUM_I2C_DEVICE} + 3 )) # MUX #3 SFP28 Port3 EEPROM 0x50
NUM_MUX_9548_CH3=$(( ${NUM_I2C_DEVICE} + 4 )) # MUX #4 SFP28 Port4 EEPROM 0x50
NUM_MUX_9548_CH4=$(( ${NUM_I2C_DEVICE} + 5 )) # MUX #5 SFP28 Port5 EEPROM 0x50
NUM_MUX_9548_CH5=$(( ${NUM_I2C_DEVICE} + 6 )) # MUX #6 SFP28 Port6 EEPROM 0x50
NUM_MUX_9548_CH6=$(( ${NUM_I2C_DEVICE} + 7 )) # MUX #7 FAN EEPROM (0x56, 0x57)
NUM_MUX_9548_CH7=$(( ${NUM_I2C_DEVICE} + 8 )) # MUX #8 PSU EEPROM (0x56, 0x57)

PATH_SYS_I2C_DEVICES="/sys/bus/i2c/devices"
PATH_I2C_1_DEVICE="${PATH_SYS_I2C_DEVICES}/i2c-${NUM_I2C_1_DEVICE}"
PATH_MUX_9548_CH0="${PATH_SYS_I2C_DEVICES}/i2c-${NUM_MUX_9548_CH0}"
PATH_MUX_9548_CH1="${PATH_SYS_I2C_DEVICES}/i2c-${NUM_MUX_9548_CH1}"
PATH_MUX_9548_CH2="${PATH_SYS_I2C_DEVICES}/i2c-${NUM_MUX_9548_CH2}"
PATH_MUX_9548_CH3="${PATH_SYS_I2C_DEVICES}/i2c-${NUM_MUX_9548_CH3}"
PATH_MUX_9548_CH4="${PATH_SYS_I2C_DEVICES}/i2c-${NUM_MUX_9548_CH4}"
PATH_MUX_9548_CH5="${PATH_SYS_I2C_DEVICES}/i2c-${NUM_MUX_9548_CH5}"
PATH_MUX_9548_CH6="${PATH_SYS_I2C_DEVICES}/i2c-${NUM_MUX_9548_CH6}"
PATH_MUX_9548_CH7="${PATH_SYS_I2C_DEVICES}/i2c-${NUM_MUX_9548_CH7}"

# I2C Address
### I2C MUX PCA9548
I2C_ADDR_MUX_9548_CH0=0x71 # SFP28 MUX #1 EEPROM
I2C_ADDR_MUX_9548_CH1=0x71 # SFP28 MUX #2 EEPROM
I2C_ADDR_MUX_9548_CH2=0x71 # SFP28 MUX #3 EEPROM
I2C_ADDR_MUX_9548_CH3=0x71 # SFP28 MUX #4 EEPROM
I2C_ADDR_MUX_9548_CH4=0x71 # SFP28 MUX #5 EEPROM
I2C_ADDR_MUX_9548_CH5=0x71 # SFP28 MUX #6 EEPROM
I2C_ADDR_MUX_9548_CH6=0x71 # FAN   MUX #7 EEPROM
I2C_ADDR_MUX_9548_CH7=0x71 # PSU   MUX #8 EEPROM
### GPIO Expander
I2C_ADDR_IO_PCAL6416=0x20  # GPIO Expander PCAL6416A  
I2C_ADDR_IO_PCAL6524=0x22  # GPIO Expander PCAL6524
### peripheral
I2C_ADDR_FAN1_EEPROM=0x56  # FAN1 EEPROM
I2C_ADDR_FAN2_EEPROM=0x57  # FAN2 EEPROM
I2C_ADDR_PSU1_EEPROM=0x56  # PSU1 EEPROM
I2C_ADDR_PSU2_EEPROM=0x57  # PSU2 EEPROM
I2C_ADDR_TMP75_1=0x48      # LM75 temperature sensor 1
I2C_ADDR_TMP75_2=0x49      # LM75 temperature sensor 2
I2C_ADDR_QSFP_EEPROM=0x50  # SFP28 port EEPROM

# IO Expander Register
# direction
PCAL6524_REG_PORT0_DIR=0x0C
PCAL6524_REG_PORT1_DIR=0x0D
PCAL6524_REG_PORT2_DIR=0x0E

PCAL6416_REG_PORT0_DIR=6
PCAL6416_REG_PORT1_DIR=7

# polarity
PCAL6524_REG_PORT0_POL=0x08
PCAL6524_REG_PORT1_POL=0x09
PCAL6524_REG_PORT2_POL=0x0A

PCAL6416_REG_PORT0_POL=4
PCAL6416_REG_PORT1_POL=5

# output
PCAL6524_REG_PORT0_OUT=0x04
PCAL6524_REG_PORT1_OUT=0x05
PCAL6524_REG_PORT2_OUT=0x06

PCAL6416_REG_PORT0_OUT=2
PCAL6416_REG_PORT1_OUT=3

# input
PCAL6524_REG_PORT0_IN=0x00
PCAL6524_REG_PORT1_IN=0x01
PCAL6524_REG_PORT2_IN=0x02

PCAL6416_REG_PORT0_IN=0
PCAL6416_REG_PORT1_IN=1

# Load required kernel-mode drivers
load_kernel_drivers() {
    # Remove modules loaded during Linux init
    # FIX-ME: This will be removed in the future when Linux init no longer loads these
    rmmod i2c_dev
    rmmod i2c_mv64xxx
    rmmod i2c_mux_pca954x

    # Carefully control the load order here to ensure consistent i2c bus numbering
    modprobe i2c_mux_pca954x force_deselect_on_exit=1
    modprobe i2c_mv64xxx
    modprobe i2c_dev
    modprobe eeprom
    modprobe mvMbusDrv
}

# i2c MUX PCA9548 init
i2c_mux_init() {
    # add MUX PCA9548 on I2C_1, assume to be i2c-2~9
    if [ ! -e ${PATH_MUX_9548_CH0} ]; then
        _retry "echo 'pca9548 ${I2C_ADDR_MUX_9548_CH0}' > ${PATH_I2C_1_DEVICE}/new_device"
    else
        echo "pca9548 ${I2C_ADDR_MUX_9548_CH0} already init."
    fi

}

# I/O Expander init
#----------------------------------------------------------------------------
# PCAL6524 -- [I2C 0x22]    24 bits I/O for SFP status and TX_DIS
#   Port 0 --    7      6      5      4        3      2      1      0
#            TX_FAULT TX_DIS  LOS  PRESENT TX_FAULT TX_DIS  LOS  PRESENT
#              SFP1    SFP1   SFP1  SFP1     SFP0    SFP0   SFP0  SFP0
#
#   Port 1 --    7      6      5      4        3      2      1      0
#            TX_FAULT TX_DIS  LOS  PRESENT TX_FAULT TX_DIS  LOS  PRESENT
#              SFP3    SFP3   SFP3  SFP3     SFP2    SFP2   SFP2  SFP2
#
#   Port 1 --    7      6      5      4        3      2      1      0
#            TX_FAULT TX_DIS  LOS  PRESENT TX_FAULT TX_DIS  LOS  PRESENT
#              SFP5    SFP5   SFP5  SFP5     SFP4    SFP4   SFP4  SFP4
# [TX_DIS bit is output, all other bits are input]
#---------------------------------------------------------------------------
# PCAL6416A -- [I2C 0x20]  16 bits I/) Expander  SFP RS0 and RS1
#    Port 0 --   7    6    5    4        3    2    1    0
#               RS0  RS1  RS0  RS1      RS0  RS1  RS0  RS1
#                  SF2       SF3          SF0       SF1
#
#    Port 0 --   7    6    5    4        3    2    1    0
#               N/A  N/A  N/A  N/A      RS0  RS1  RS0  RS1
#                                         SF4       SF5
# [ All bits are output]
# According to SFF-8431
#    RS0 - low : RX signalling rate less than or equal to 4.25GBd
#          high: RX signalling rate greater than 4.25GBd
#    RS1 - low : TX signalling rate less than or equal to 4.25GBd
#          high: TX signalling rate greater than 4.25GBd
#---------------------------------------------------------------------------

i2c_io_exp_init() {
    echo "Init SFP status and ctrl IO Expander"
    sudo i2cset -y -r ${NUM_I2C_1_DEVICE} ${I2C_ADDR_IO_PCAL6524} ${PCAL6524_REG_PORT0_DIR} 0xBB
    sudo i2cset -y -r ${NUM_I2C_1_DEVICE} ${I2C_ADDR_IO_PCAL6524} ${PCAL6524_REG_PORT1_DIR} 0xBB
    sudo i2cset -y -r ${NUM_I2C_1_DEVICE} ${I2C_ADDR_IO_PCAL6524} ${PCAL6524_REG_PORT2_DIR} 0xBB
    sudo i2cset -y -r ${NUM_I2C_1_DEVICE} ${I2C_ADDR_IO_PCAL6524} ${PCAL6524_REG_PORT0_POL} 0x00
    sudo i2cset -y -r ${NUM_I2C_1_DEVICE} ${I2C_ADDR_IO_PCAL6524} ${PCAL6524_REG_PORT1_POL} 0x00
    sudo i2cset -y -r ${NUM_I2C_1_DEVICE} ${I2C_ADDR_IO_PCAL6524} ${PCAL6524_REG_PORT2_POL} 0x00

    echo "Init SFP RS0 and RS1 IO Expander"
    sudo i2cset -y -r ${NUM_I2C_1_DEVICE} ${I2C_ADDR_IO_PCAL6416} ${PCAL6416_REG_PORT0_DIR} 0x00
    sudo i2cset -y -r ${NUM_I2C_1_DEVICE} ${I2C_ADDR_IO_PCAL6416} ${PCAL6416_REG_PORT1_DIR} 0x00
    sudo i2cset -y -r ${NUM_I2C_1_DEVICE} ${I2C_ADDR_IO_PCAL6416} ${PCAL6416_REG_PORT0_POL} 0x00
    sudo i2cset -y -r ${NUM_I2C_1_DEVICE} ${I2C_ADDR_IO_PCAL6416} ${PCAL6416_REG_PORT1_POL} 0x00
    sudo i2cset -y -r ${NUM_I2C_1_DEVICE} ${I2C_ADDR_IO_PCAL6416} ${PCAL6416_REG_PORT0_OUT} 0xFF
    sudo i2cset -y -r ${NUM_I2C_1_DEVICE} ${I2C_ADDR_IO_PCAL6416} ${PCAL6416_REG_PORT1_OUT} 0xFF
}

# - Main entry

# Install kernel drivers required for i2c bus access
load_kernel_drivers
#entropy setting

# LOGIC to enumerate SFP eeprom devices - send 0x50 to kernel i2c driver - initialize devices
# the mux may be enumerated at number 4 or 5 so we check for the mux and skip if needed
echo pca9548 ${I2C_ADDR_MUX_9548_CH0} > ${PATH_I2C_1_DEVICE}/new_device

# Get list of the mux channels
ismux_bus=$(i2cdetect -l|grep mux|cut -f1)

# Enumerate the SFP eeprom device on each mux channel

for mux in ${ismux_bus}
do
    if [[ "${mux}" != "i2c-8" ]] && [[ "${mux}" != "i2c-9" ]]; then
        echo optoe2 ${I2C_ADDR_QSFP_EEPROM} > /sys/class/i2c-adapter/${mux}/new_device
	mux_num=$(echo ${mux} | cut -b5)
	chmod 644 /sys/class/i2c-adapter/${mux}/${mux_num}-0050/eeprom
    fi

    if [ "${mux}" == "i2c-8" ]; then
        # Enumerate fan eeprom devices
        echo eeprom 0x56 > /sys/class/i2c-adapter/i2c-8/new_device
        chmod 644 /sys/class/i2c-adapter/i2c-8/8-0056/eeprom

        echo eeprom 0x57 > /sys/class/i2c-adapter/i2c-8/new_device
        chmod 644 /sys/class/i2c-adapter/i2c-8/8-0057/eeprom
    fi

    if [ "${mux}" == "i2c-9" ]; then
        # Enumerate fan eeprom devices
        echo eeprom 0x56 > /sys/class/i2c-adapter/i2c-9/new_device
        chmod 644 /sys/class/i2c-adapter/i2c-9/9-0056/eeprom

        echo eeprom 0x57 > /sys/class/i2c-adapter/i2c-9/new_device
        chmod 644 /sys/class/i2c-adapter/i2c-9/9-0057/eeprom
    fi
done

# Enumerate rtc 
echo  pcf8563 0x51 > /sys/bus/i2c/devices/i2c-0/new_device
# Enumerate system eeprom
echo 24c02 0x54 > /sys/class/i2c-adapter/i2c-0/new_device

# Enumerate PD eeprom
echo 24c02 0x52 > /sys/class/i2c-adapter/i2c-0/new_device

# Enumerate AC5X eeprom
echo 24c64 0x53 > /sys/class/i2c-adapter/i2c-0/new_device

# Enumerate temperature sensors
echo lm75 0x48 > /sys/class/i2c-adapter/i2c-0/new_device

echo lm75 0x49 > /sys/class/i2c-adapter/i2c-0/new_device

# Enumerate gpio
echo gpio 0x22 > /sys/class/i2c-adapter/i2c-1/new_device
echo gpio 0x20 > /sys/class/i2c-adapter/i2c-1/new_device

# Enumerate cpld
echo cpld 0x66 > /sys/class/i2c-adapter/i2c-0/new_device

sleep 1
chmod 644 /sys/class/i2c-adapter/i2c-0/0-0054/eeprom
chmod 644 /sys/class/i2c-adapter/i2c-0/0-0052/eeprom
chmod 644 /sys/class/i2c-adapter/i2c-0/0-0053/eeprom

i2c_io_exp_init

#setting boot_once to undefined everytime after reboot
/usr/bin/fw_setenv boot_once

hwclock -s

exit 0
