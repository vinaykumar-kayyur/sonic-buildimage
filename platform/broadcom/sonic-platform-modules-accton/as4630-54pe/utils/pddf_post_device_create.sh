#!/bin/bash

set_pca_mux_idle_disconnect()
{
    echo -2 | tee /sys/bus/i2c/drivers/pca954x/*-00*/idle_state >& /dev/null
    if [ $? -ne 0 ]; then
        echo "Fail to set pca954x mux idle disconnect"
        exit 2
    fi
}

echo "Setting LED MAC Mode.."
i2cset -y -f 3 0x60 0x2a 0xff
i2cset -y -f 3 0x60 0x2b 0xff
i2cset -y -f 3 0x60 0x86 0x89
echo "Setting LED MAC Mode..DONE"
# Turn off STK1 and STK2 LED. Bit5:4 to 0x11
#i2cset -y -f 3 0x60 0xb5
stk_val=$(i2cget -y -f 3 0x60 0x31)
new_val=$((${stk_val}|0x30))
i2cset -y -f 3 0x60 0x31 ${new_val}
echo "STK LEDs are turned off successfully"

set_pca_mux_idle_disconnect
