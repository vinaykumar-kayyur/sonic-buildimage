#!/bin/bash

dis_i2c_ir3570a()
{
    local addr=$1

    i2cset -y 0 $addr 0xE5 0x01 &>/dev/null
    i2cset -y 0 $addr 0x12 0x02 &>/dev/null
}


ir3570_check()
{
    dump=`i2cdump -y 0 0x42 s 0x9a |awk 'END {print $2}'`
    if [ $dump -eq 24 ]; then
        echo "Disabling i2c function of ir3570a"
        dis_i2c_ir3570a 0x4
    fi
}

ir3570_check

# Steps to check syseeprom i2c address
use_57_eeprom=false
i2cget -y -f 0 0x57 0x0 &>/dev/null
if [ $? -eq 0 ]; then
    use_57_eeprom=true
fi
echo "The board is using 0x57 address: $use_57_eeprom"

if $use_57_eeprom ; then
    # syseeprom is at the i2c address 0x57. Change the .json file
    sed -i 's@"topo_info": {"parent_bus": "0x0", "dev_addr": "0x56", "dev_type": "24c02"},@"topo_info": {"parent_bus": "0x0", "dev_addr": "0x57", "dev_type": "24c02"},@g' ./pddf-device.json
fi
