# Perform an i2c device configuration : instantiate / delete.
# Input is of the form:
# "echo [driver] <i2c-address> >  <i2c-bus/operation>"
# where operation = "new_device" or "delete_device"

i2c_config() {
    local count=0
    local MAX_BUS_RETRY=20
    local MAX_I2C_OP_RETRY=10

    i2c_bus_op=`echo "$@" | cut -d'>' -f 2`
    i2c_bus=$(dirname $i2c_bus_op)

    # check if bus exists
    while [[ "$count" -lt "$MAX_BUS_RETRY" ]]; do
        [[ -e $i2c_bus ]] && break || sleep .1
        count=$((count+1))
    done

    if [[ "$count" -eq "$MAX_BUS_RETRY" ]]; then
        echo "ERROR: $@ : i2c bus not created"
        return
    fi

    # perform the add/delete
    count=0
    while [[ "$count" -lt "$MAX_I2C_OP_RETRY" ]]; do
        eval "$@" > /dev/null 2>&1
        [[ $? == 0 ]] && break || sleep .2
        count=$((count+1))
    done

    if [[ "$count" -eq "$MAX_I2C_OP_RETRY" ]]; then
        echo "ERROR: $@ : i2c operation failed"
        return
    fi
}

# Check if a i2c bus exists. Poll for upto 2 seconds since mux creation may take time..
# Input: bus to check for existence

i2c_poll_bus_exists() {
    local count=0
    local MAX_BUS_RETRY=20
    local i2c_bus

    i2c_bus=$1

    # check if bus exists
    while [[ "$count" -lt "$MAX_BUS_RETRY" ]]; do
        [[ -e $i2c_bus ]] && break || sleep .1
        count=$((count+1))
    done

    if [[ "$count" -eq "$MAX_BUS_RETRY" ]]; then
        echo "ERROR: $@ : i2c bus not created"
        return 1
    else
        return 0
    fi
}

# Perform an i2c mux device create
# Input is of the form:
# "echo [mux driver] <i2c-mux-address> >  <i2c-bus/operation>" i2c-channel-first
# where operation = "new_device"
# i2c-channel-first is the first of the 8 channels that this mux should create
i2c_mux_create() {
    local MAX_MUX_CHANNEL_RETRY=5
    local MAX_MUX_CHANNELS=8
    local count=0
    local i
    local i2c_bus_op
    local i2c_bus
    local i2c_bus_num
    local i2c_mux
    local i2c_mux_channel_first
    local i2c_mux_channel_last

    # Extract the i2c parameters from the command line
    i2c_bus_op=`echo "$1" | cut -d'>' -f 2`
    i2c_bus=$(dirname $i2c_bus_op)
    i2c_bus_num=`echo $(basename $i2c_bus) | cut -d'-' -f 2`
    i2c_mux=`echo "$1" | cut -d' ' -f 3 | sed 's/^0x//'`
    i2c_mux_channel_first=$i2c_bus/i2c-$2
    i2c_mux_channel_last=$i2c_bus/i2c-$(expr $2 + $MAX_MUX_CHANNELS - 1)

    if  i2c_poll_bus_exists  $i2c_bus; then
        while [[ "$count" -lt "$MAX_MUX_CHANNEL_RETRY" ]]; do
            eval "$1" > /dev/null 2>&1
            ret=$?

            # Give more time for the mux channels to get created based on retries
            i=0
            while [[ "$i" -lt "$count" ]]; do
                sleep .5
                i=$((i+1))
            done

            # Check if the (first and last) mux channels got created
            if [[ $ret -eq "0" && -e $i2c_mux_channel_first && -e $i2c_mux_channel_last ]]; then
                break;
            else
                # If the channel did not get created, remove the mux, reset the mux tree and retry
                i2c_config "echo 0x$i2c_mux > /sys/bus/i2c/devices/i2c-$devnum/i2c-$i2c_bus_num/delete_device"
                reset_muxes
            fi

            count=$((count+1))
        done
    fi

    if [[ "$count" -eq "$MAX_MUX_CHANNEL_RETRY" ]]; then
        echo "ERROR: $1,$2 : i2c mux channel not created"
        return
    fi

    return
}
