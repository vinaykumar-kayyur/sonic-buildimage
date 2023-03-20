# coding:utf-8

psu_fan_airflow = {
    "intake": ['DPS-1300AB-6 S', 'GW-CRPS1300D'],
    "exhaust": ['CSU550AP-3-501', 'DPS-550AB-40 A'],
}

fanairflow = {
    "intake": ['P2EFAN I-F'],
    "exhaust": [],
}

psu_display_name = {
    "PA1300I-F": ['GW-CRPS1300D', 'DPS-1300AB-6 S'],
}

psutypedecode = {
    0x00: 'N/A',
    0x01: 'AC',
    0x02: 'DC',
}


class Unit:
    Temperature = "C"
    Voltage = "V"
    Current = "A"
    Power = "W"
    Speed = "RPM"


class threshold:
    PSU_TEMP_MIN = -10 * 1000
    PSU_TEMP_MAX = 60 * 1000

    PSU_FAN_SPEED_MIN = 150
    PSU_FAN_SPEED_MAX = 12000

    PSU_OUTPUT_VOLTAGE_MIN = 11 * 1000
    PSU_OUTPUT_VOLTAGE_MAX = 14 * 1000

    PSU_AC_INPUT_VOLTAGE_MIN = 200 * 1000
    PSU_AC_INPUT_VOLTAGE_MAX = 240 * 1000

    PSU_DC_INPUT_VOLTAGE_MIN = 190 * 1000
    PSU_DC_INPUT_VOLTAGE_MAX = 290 * 1000

    ERR_VALUE = -9999999

    PSU_OUTPUT_POWER_MIN = 10 * 1000 * 1000
    PSU_OUTPUT_POWER_MAX = 1300 * 1000 * 1000

    PSU_INPUT_POWER_MIN = 10 * 1000 * 1000
    PSU_INPUT_POWER_MAX = 1444 * 1000 * 1000

    PSU_OUTPUT_CURRENT_MIN = 2 * 1000
    PSU_OUTPUT_CURRENT_MAX = 107 * 1000

    PSU_INPUT_CURRENT_MIN = 0.2 * 1000
    PSU_INPUT_CURRENT_MAX = 7 * 1000

    FRONT_FAN_SPEED_MAX = 11000
    REAR_FAN_SPEED_MAX = 9500
    FAN_SPEED_MIN = 1500


class Description:
    CPLD = "Used for managing IO modules, SFP+ modules and system LEDs"
    BIOS = "Performs initialization of hardware components during booting"
    FPGA = "Platform management controller for on-board temperature monitoring, in-chassis power"


devices = {
    "onie_e2": [
        {
            "name": "ONIE_E2",
            "e2loc": {"loc": "/sys/bus/i2c/devices/1-0056/eeprom", "way": "sysfs"},
        },
    ],
    "psus": [
        {
            "e2loc": {"loc": "/sys/bus/i2c/devices/23-0050/eeprom", "way": "sysfs"},
            "pmbusloc": {"bus": 23, "addr": 0x58, "way": "i2c"},
            "present": {"loc": "/sys/devices/pci0000:00/0000:00:1f.0/psu_status_1", "way": "sysfs", "mask": 0x01},
            "name": "PSU1",
            "psu_display_name": psu_display_name,
            "airflow": psu_fan_airflow,
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/23-0058/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": threshold.PSU_TEMP_MIN,
                "Max": threshold.PSU_TEMP_MAX,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            },
            "FanSpeed": {
                "value": {"loc": "/sys/bus/i2c/devices/23-0058/hwmon/hwmon*/fan1_input", "way": "sysfs"},
                "Min": threshold.PSU_FAN_SPEED_MIN,
                "Max": threshold.PSU_FAN_SPEED_MAX,
                "Unit": Unit.Speed
            },
            "InputsStatus": {"bus": 23, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x2000},
            "InputsType": {"bus": 23, "addr": 0x58, "offset": 0x80, "way": "i2c", 'psutypedecode': psutypedecode},
            "InputsVoltage": {
                'AC': {
                    "value": {"loc": "/sys/bus/i2c/devices/23-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_AC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_AC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'DC': {
                    "value": {"loc": "/sys/bus/i2c/devices/23-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_DC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_DC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'other': {
                    "value": {"loc": "/sys/bus/i2c/devices/23-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.ERR_VALUE,
                    "Max": threshold.ERR_VALUE,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                }
            },
            "InputsCurrent":
            {
                "value": {"loc": "/sys/bus/i2c/devices/23-0058/hwmon/hwmon*/curr1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_CURRENT_MIN,
                "Max": threshold.PSU_INPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "InputsPower":
            {
                "value": {"loc": "/sys/bus/i2c/devices/23-0058/hwmon/hwmon*/power1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_POWER_MIN,
                "Max": threshold.PSU_INPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
            "OutputsStatus": {"bus": 23, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x8800},
            "OutputsVoltage":
            {
                "value": {"loc": "/sys/bus/i2c/devices/23-0058/hwmon/hwmon*/in2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_VOLTAGE_MIN,
                "Max": threshold.PSU_OUTPUT_VOLTAGE_MAX,
                "Unit": Unit.Voltage,
                "format": "float(float(%s)/1000)"
            },
            "OutputsCurrent":
            {
                "value": {"loc": "/sys/bus/i2c/devices/23-0058/hwmon/hwmon*/curr2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_CURRENT_MIN,
                "Max": threshold.PSU_OUTPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "OutputsPower":
            {
                "value": {"loc": "/sys/bus/i2c/devices/23-0058/hwmon/hwmon*/power2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_POWER_MIN,
                "Max": threshold.PSU_OUTPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
        },
        {
            "e2loc": {"loc": "/sys/bus/i2c/devices/25-0050/eeprom", "way": "sysfs"},
            "pmbusloc": {"bus": 25, "addr": 0x58, "way": "i2c"},
            "present": {"loc": "/sys/devices/pci0000:00/0000:00:1f.0/psu_status_2", "way": "sysfs", "mask": 0x01},
            "name": "PSU2",
            "psu_display_name": psu_display_name,
            "airflow": psu_fan_airflow,
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/25-0058/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": threshold.PSU_TEMP_MIN,
                "Max": threshold.PSU_TEMP_MAX,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            },
            "FanSpeed": {
                "value": {"loc": "/sys/bus/i2c/devices/25-0058/hwmon/hwmon*/fan1_input", "way": "sysfs"},
                "Min": threshold.PSU_FAN_SPEED_MIN,
                "Max": threshold.PSU_FAN_SPEED_MAX,
                "Unit": Unit.Speed
            },
            "InputsStatus": {"bus": 25, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x2000},
            "InputsType": {"bus": 25, "addr": 0x58, "offset": 0x80, "way": "i2c", 'psutypedecode': psutypedecode},
            "InputsVoltage": {
                'AC': {
                    "value": {"loc": "/sys/bus/i2c/devices/25-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_AC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_AC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'DC': {
                    "value": {"loc": "/sys/bus/i2c/devices/25-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_DC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_DC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'other': {
                    "value": {"loc": "/sys/bus/i2c/devices/25-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.ERR_VALUE,
                    "Max": threshold.ERR_VALUE,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                }
            },
            "InputsCurrent":
            {
                "value": {"loc": "/sys/bus/i2c/devices/25-0058/hwmon/hwmon*/curr1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_CURRENT_MIN,
                "Max": threshold.PSU_INPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "InputsPower":
            {
                "value": {"loc": "/sys/bus/i2c/devices/25-0058/hwmon/hwmon*/power1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_POWER_MIN,
                "Max": threshold.PSU_INPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
            "OutputsStatus": {"bus": 25, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x8800},
            "OutputsVoltage":
            {
                "value": {"loc": "/sys/bus/i2c/devices/25-0058/hwmon/hwmon*/in2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_VOLTAGE_MIN,
                "Max": threshold.PSU_OUTPUT_VOLTAGE_MAX,
                "Unit": Unit.Voltage,
                "format": "float(float(%s)/1000)"
            },
            "OutputsCurrent":
            {
                "value": {"loc": "/sys/bus/i2c/devices/25-0058/hwmon/hwmon*/curr2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_CURRENT_MIN,
                "Max": threshold.PSU_OUTPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "OutputsPower":
            {
                "value": {"loc": "/sys/bus/i2c/devices/25-0058/hwmon/hwmon*/power2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_POWER_MIN,
                "Max": threshold.PSU_OUTPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
        },
        {
            "e2loc": {"loc": "/sys/bus/i2c/devices/24-0050/eeprom", "way": "sysfs"},
            "pmbusloc": {"bus": 24, "addr": 0x58, "way": "i2c"},
            "present": {"loc": "/sys/devices/pci0000:00/0000:00:1f.0/psu_status_3", "way": "sysfs", "mask": 0x01},
            "name": "PSU3",
            "psu_display_name": psu_display_name,
            "airflow": psu_fan_airflow,
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/24-0058/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": threshold.PSU_TEMP_MIN,
                "Max": threshold.PSU_TEMP_MAX,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            },
            "FanSpeed": {
                "value": {"loc": "/sys/bus/i2c/devices/24-0058/hwmon/hwmon*/fan1_input", "way": "sysfs"},
                "Min": threshold.PSU_FAN_SPEED_MIN,
                "Max": threshold.PSU_FAN_SPEED_MAX,
                "Unit": Unit.Speed
            },
            "InputsStatus": {"bus": 24, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x2000},
            "InputsType": {"bus": 24, "addr": 0x58, "offset": 0x80, "way": "i2c", 'psutypedecode': psutypedecode},
            "InputsVoltage": {
                'AC': {
                    "value": {"loc": "/sys/bus/i2c/devices/24-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_AC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_AC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'DC': {
                    "value": {"loc": "/sys/bus/i2c/devices/24-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_DC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_DC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'other': {
                    "value": {"loc": "/sys/bus/i2c/devices/24-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.ERR_VALUE,
                    "Max": threshold.ERR_VALUE,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                }
            },
            "InputsCurrent":
            {
                "value": {"loc": "/sys/bus/i2c/devices/24-0058/hwmon/hwmon*/curr1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_CURRENT_MIN,
                "Max": threshold.PSU_INPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "InputsPower":
            {
                "value": {"loc": "/sys/bus/i2c/devices/24-0058/hwmon/hwmon*/power1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_POWER_MIN,
                "Max": threshold.PSU_INPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
            "OutputsStatus": {"bus": 24, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x8800},
            "OutputsVoltage":
            {
                "value": {"loc": "/sys/bus/i2c/devices/24-0058/hwmon/hwmon*/in2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_VOLTAGE_MIN,
                "Max": threshold.PSU_OUTPUT_VOLTAGE_MAX,
                "Unit": Unit.Voltage,
                "format": "float(float(%s)/1000)"
            },
            "OutputsCurrent":
            {
                "value": {"loc": "/sys/bus/i2c/devices/24-0058/hwmon/hwmon*/curr2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_CURRENT_MIN,
                "Max": threshold.PSU_OUTPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "OutputsPower":
            {
                "value": {"loc": "/sys/bus/i2c/devices/24-0058/hwmon/hwmon*/power2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_POWER_MIN,
                "Max": threshold.PSU_OUTPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
        },
        {
            "e2loc": {"loc": "/sys/bus/i2c/devices/26-0050/eeprom", "way": "sysfs"},
            "pmbusloc": {"bus": 26, "addr": 0x58, "way": "i2c"},
            "present": {"loc": "/sys/devices/pci0000:00/0000:00:1f.0/psu_status_4", "way": "sysfs", "mask": 0x01},
            "name": "PSU4",
            "psu_display_name": psu_display_name,
            "airflow": psu_fan_airflow,
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/26-0058/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": threshold.PSU_TEMP_MIN,
                "Max": threshold.PSU_TEMP_MAX,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            },
            "FanSpeed": {
                "value": {"loc": "/sys/bus/i2c/devices/26-0058/hwmon/hwmon*/fan1_input", "way": "sysfs"},
                "Min": threshold.PSU_FAN_SPEED_MIN,
                "Max": threshold.PSU_FAN_SPEED_MAX,
                "Unit": Unit.Speed
            },
            "InputsStatus": {"bus": 26, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x2000},
            "InputsType": {"bus": 26, "addr": 0x58, "offset": 0x80, "way": "i2c", 'psutypedecode': psutypedecode},
            "InputsVoltage": {
                'AC': {
                    "value": {"loc": "/sys/bus/i2c/devices/26-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_AC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_AC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'DC': {
                    "value": {"loc": "/sys/bus/i2c/devices/26-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_DC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_DC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'other': {
                    "value": {"loc": "/sys/bus/i2c/devices/26-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.ERR_VALUE,
                    "Max": threshold.ERR_VALUE,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                }
            },
            "InputsCurrent":
            {
                "value": {"loc": "/sys/bus/i2c/devices/26-0058/hwmon/hwmon*/curr1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_CURRENT_MIN,
                "Max": threshold.PSU_INPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "InputsPower":
            {
                "value": {"loc": "/sys/bus/i2c/devices/26-0058/hwmon/hwmon*/power1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_POWER_MIN,
                "Max": threshold.PSU_INPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
            "OutputsStatus": {"bus": 26, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x8800},
            "OutputsVoltage":
            {
                "value": {"loc": "/sys/bus/i2c/devices/26-0058/hwmon/hwmon*/in2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_VOLTAGE_MIN,
                "Max": threshold.PSU_OUTPUT_VOLTAGE_MAX,
                "Unit": Unit.Voltage,
                "format": "float(float(%s)/1000)"
            },
            "OutputsCurrent":
            {
                "value": {"loc": "/sys/bus/i2c/devices/26-0058/hwmon/hwmon*/curr2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_CURRENT_MIN,
                "Max": threshold.PSU_OUTPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "OutputsPower":
            {
                "value": {"loc": "/sys/bus/i2c/devices/26-0058/hwmon/hwmon*/power2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_POWER_MIN,
                "Max": threshold.PSU_OUTPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
        },
    ],
    "temps": [
        {
            "name": "BOARD_TEMP",
            "temp_id": "TEMP1",
            "Temperature": {
                "value": [
                    {"loc": "/sys/bus/i2c/devices/32-0048/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/32-004d/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/48-0048/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/48-004d/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/40-0048/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/40-004d/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/16-0048/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/16-004d/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                ],
                "Min": -10000,
                "Low": 0,
                "High": 85000,
                "Max": 90000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
        {
            "name": "CPU_TEMP",
            "temp_id": "TEMP2",
            "Temperature": {
                "value": {"loc": "/sys/bus/platform/devices/coretemp.0/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": 2000,
                "Low": 10000,
                "High": 85000,
                "Max": 100000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
        {
            "name": "INLET_TEMP",
            "temp_id": "TEMP3",
            "Temperature": {
                "value": [
                    {"loc": "/sys/bus/i2c/devices/32-0049/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/48-0049/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/40-0049/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/16-0049/hwmon/hwmon*/temp1_input", "way": "sysfs"}
                ],
                "Min": -10000,
                "Low": 0,
                "High": 50000,
                "Max": 60000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
        {
            "name": "OUTLET_TEMP",
            "temp_id": "TEMP4",
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/28-004b/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": -10000,
                "Low": 0,
                "High": 85000,
                "Max": 90000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
        {
            "name": "SWITCH_TEMP",
            "temp_id": "TEMP5",
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/28-004c/hwmon/hwmon*/temp2_input", "way": "sysfs"},
                "Min": 2000,
                "Low": 10000,
                "High": 100000,
                "Max": 105000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
        {
            "name": "SFF_TEMP",
            "Temperature": {
                "value": {"loc": "/tmp/highest_sff_temp", "way": "sysfs", "flock_path": "/tmp/highest_sff_temp"},
                "Min": -15000,
                "Low": 0,
                "High": 80000,
                "Max": 100000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
    ],
    "leds": [
        {
            "name": "BOARD_SYS_LED",
            "led_type": "SYS_LED",
            "led": {"loc": "/sys/devices/pci0000:00/0000:00:1f.0/broad_front_sys", "way": "sysfs"},
            "led_attrs": {
                "green": 0x04, "red": 0x02, "amber": 0x06, "default": 0x04,
                "flash": 0xff, "light": 0xff, "off": 0, "mask": 0xff
            },
        },
        {
            "name": "BOARD_PSU_LED",
            "led_type": "PSU_LED",
            "led": {"loc": "/sys/devices/pci0000:00/0000:00:1f.0/broad_front_pwr", "way": "sysfs"},
            "led_attrs": {
                "green": 0x04, "red": 0x02, "amber": 0x06, "default": 0x04,
                "flash": 0xff, "light": 0xff, "off": 0, "mask": 0xff
            },
        },
        {
            "name": "BOARD_FAN_LED",
            "led_type": "FAN_LED",
            "led": {"loc": "/sys/devices/pci0000:00/0000:00:1f.0/broad_front_fan", "way": "sysfs"},
            "led_attrs": {
                "green": 0x04, "red": 0x02, "amber": 0x06, "default": 0x04,
                "flash": 0xff, "light": 0xff, "off": 0, "mask": 0xff
            },
        },
    ],
    "fans": [
        {
            "name": "FAN1",
            "airflow": fanairflow,
            "e2loc": {"loc": "/sys/bus/i2c/devices/63-0050/eeprom", "way": "sysfs"},
            "present": {"bus": 14, "addr": 0x0d, "offset": 0x30, "way": "i2c", "mask": 0x01},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 14, "addr": 0x0d, "offset": 0x3b, "way": "i2c"},
            "led_attrs": {
                "green": 0x04, "red": 0x02, "amber": 0x06, "default": 0x04,
                "flash": 0xff, "light": 0xff, "off": 0xff
            },
            "Rotor": {
                "Rotor1_config": {"name": "Rotor1",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                  "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 14, "addr": 0x0d, "offset": 0x14, "way": "i2c"},
                                  "Running": {"bus": 14, "addr": 0x0d, "offset": 0x31, "way": "i2c", "mask": 0x01, "is_runing": 0x01},
                                  "HwAlarm": {"bus": 14, "addr": 0x0d, "offset": 0x31, "way": "i2c", "mask": 0x01, "no_alarm": 0x01},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/14-000d/fan1_1_real_speed", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.FRONT_FAN_SPEED_MAX,
                                      "Unit": Unit.Speed,
                                  },
                                  },
                "Rotor2_config": {"name": "Rotor2",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                          "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 14, "addr": 0x0d, "offset": 0x14, "way": "i2c"},
                                  "Running": {"bus": 14, "addr": 0x0d, "offset": 0x34, "way": "i2c", "mask": 0x01, "is_runing": 0x01},
                                  "HwAlarm": {"bus": 14, "addr": 0x0d, "offset": 0x34, "way": "i2c", "mask": 0x01, "no_alarm": 0x01},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/14-000d/fan1_2_real_speed", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.REAR_FAN_SPEED_MAX,
                                      "Unit": Unit.Speed,
                                  },
                                  },
            },
        },
        {
            "name": "FAN2",
            "airflow": fanairflow,
            "e2loc": {"loc": "/sys/bus/i2c/devices/55-0050/eeprom", "way": "sysfs"},
            "present": {"bus": 13, "addr": 0x0d, "offset": 0x30, "way": "i2c", "mask": 0x01},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 13, "addr": 0x0d, "offset": 0x3b, "way": "i2c"},
            "led_attrs": {
                "green": 0x04, "red": 0x02, "amber": 0x06, "default": 0x04,
                "flash": 0xff, "light": 0xff, "off": 0xff
            },
            "Rotor": {
                "Rotor1_config": {"name": "Rotor1",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                  "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 13, "addr": 0x0d, "offset": 0x14, "way": "i2c"},
                                  "Running": {"bus": 13, "addr": 0x0d, "offset": 0x31, "way": "i2c", "mask": 0x01, "is_runing": 0x01},
                                  "HwAlarm": {"bus": 13, "addr": 0x0d, "offset": 0x31, "way": "i2c", "mask": 0x01, "no_alarm": 0x01},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/13-000d/fan2_1_real_speed", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.FRONT_FAN_SPEED_MAX,
                                      "Unit": Unit.Speed,
                                  },
                                  },
                "Rotor2_config": {"name": "Rotor2",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                          "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 13, "addr": 0x0d, "offset": 0x14, "way": "i2c"},
                                  "Running": {"bus": 13, "addr": 0x0d, "offset": 0x34, "way": "i2c", "mask": 0x01, "is_runing": 0x01},
                                  "HwAlarm": {"bus": 13, "addr": 0x0d, "offset": 0x34, "way": "i2c", "mask": 0x01, "no_alarm": 0x01},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/13-000d/fan2_2_real_speed", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.REAR_FAN_SPEED_MAX,
                                      "Unit": Unit.Speed,
                                  },
                                  },
            },
        },
        {
            "name": "FAN3",
            "airflow": fanairflow,
            "e2loc": {"loc": "/sys/bus/i2c/devices/64-0050/eeprom", "way": "sysfs"},
            "present": {"bus": 14, "addr": 0x0d, "offset": 0x30, "way": "i2c", "mask": 0x02},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 14, "addr": 0x0d, "offset": 0x3c, "way": "i2c"},
            "led_attrs": {
                "green": 0x04, "red": 0x02, "amber": 0x06, "default": 0x04,
                "flash": 0xff, "light": 0xff, "off": 0xff
            },
            "Rotor": {
                "Rotor1_config": {"name": "Rotor1",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                  "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 14, "addr": 0x0d, "offset": 0x15, "way": "i2c"},
                                  "Running": {"bus": 14, "addr": 0x0d, "offset": 0x31, "way": "i2c", "mask": 0x02, "is_runing": 0x02},
                                  "HwAlarm": {"bus": 14, "addr": 0x0d, "offset": 0x31, "way": "i2c", "mask": 0x02, "no_alarm": 0x02},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/14-000d/fan3_1_real_speed", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.FRONT_FAN_SPEED_MAX,
                                      "Unit": Unit.Speed,
                                  },
                                  },
                "Rotor2_config": {"name": "Rotor2",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                          "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 14, "addr": 0x0d, "offset": 0x15, "way": "i2c"},
                                  "Running": {"bus": 14, "addr": 0x0d, "offset": 0x34, "way": "i2c", "mask": 0x02, "is_runing": 0x02},
                                  "HwAlarm": {"bus": 14, "addr": 0x0d, "offset": 0x34, "way": "i2c", "mask": 0x02, "no_alarm": 0x02},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/14-000d/fan3_2_real_speed", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.REAR_FAN_SPEED_MAX,
                                      "Unit": Unit.Speed,
                                  },
                                  },
            },
        },
        {
            "name": "FAN4",
            "airflow": fanairflow,
            "e2loc": {"loc": "/sys/bus/i2c/devices/56-0050/eeprom", "way": "sysfs"},
            "present": {"bus": 13, "addr": 0x0d, "offset": 0x30, "way": "i2c", "mask": 0x02},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 13, "addr": 0x0d, "offset": 0x3c, "way": "i2c"},
            "led_attrs": {
                "green": 0x04, "red": 0x02, "amber": 0x06, "default": 0x04,
                "flash": 0xff, "light": 0xff, "off": 0xff
            },
            "Rotor": {
                "Rotor1_config": {"name": "Rotor1",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                  "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 13, "addr": 0x0d, "offset": 0x15, "way": "i2c"},
                                  "Running": {"bus": 13, "addr": 0x0d, "offset": 0x31, "way": "i2c", "mask": 0x02, "is_runing": 0x02},
                                  "HwAlarm": {"bus": 13, "addr": 0x0d, "offset": 0x31, "way": "i2c", "mask": 0x02, "no_alarm": 0x02},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/13-000d/fan4_1_real_speed", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.FRONT_FAN_SPEED_MAX,
                                      "Unit": Unit.Speed,
                                  },
                                  },
                "Rotor2_config": {"name": "Rotor2",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                          "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 13, "addr": 0x0d, "offset": 0x15, "way": "i2c"},
                                  "Running": {"bus": 13, "addr": 0x0d, "offset": 0x34, "way": "i2c", "mask": 0x02, "is_runing": 0x02},
                                  "HwAlarm": {"bus": 13, "addr": 0x0d, "offset": 0x34, "way": "i2c", "mask": 0x02, "no_alarm": 0x02},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/13-000d/fan4_2_real_speed", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.REAR_FAN_SPEED_MAX,
                                      "Unit": Unit.Speed,
                                  },
                                  },
            },
        },
        {
            "name": "FAN5",
            "airflow": fanairflow,
            "e2loc": {"loc": "/sys/bus/i2c/devices/65-0050/eeprom", "way": "sysfs"},
            "present": {"bus": 14, "addr": 0x0d, "offset": 0x30, "way": "i2c", "mask": 0x04},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 14, "addr": 0x0d, "offset": 0x3d, "way": "i2c"},
            "led_attrs": {
                "green": 0x04, "red": 0x02, "amber": 0x06, "default": 0x04,
                "flash": 0xff, "light": 0xff, "off": 0xff
            },
            "Rotor": {
                "Rotor1_config": {"name": "Rotor1",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                  "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 14, "addr": 0x0d, "offset": 0x16, "way": "i2c"},
                                  "Running": {"bus": 14, "addr": 0x0d, "offset": 0x31, "way": "i2c", "mask": 0x04, "is_runing": 0x04},
                                  "HwAlarm": {"bus": 14, "addr": 0x0d, "offset": 0x31, "way": "i2c", "mask": 0x04, "no_alarm": 0x04},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/14-000d/fan5_1_real_speed", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.FRONT_FAN_SPEED_MAX,
                                      "Unit": Unit.Speed,
                                  },
                                  },
                "Rotor2_config": {"name": "Rotor2",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                          "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 14, "addr": 0x0d, "offset": 0x16, "way": "i2c"},
                                  "Running": {"bus": 14, "addr": 0x0d, "offset": 0x34, "way": "i2c", "mask": 0x04, "is_runing": 0x04},
                                  "HwAlarm": {"bus": 14, "addr": 0x0d, "offset": 0x34, "way": "i2c", "mask": 0x04, "no_alarm": 0x04},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/14-000d/fan5_2_real_speed", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.REAR_FAN_SPEED_MAX,
                                      "Unit": Unit.Speed,
                                  },
                                  },
            },
        },
        {
            "name": "FAN6",
            "airflow": fanairflow,
            "e2loc": {"loc": "/sys/bus/i2c/devices/57-0050/eeprom", "way": "sysfs"},
            "present": {"bus": 13, "addr": 0x0d, "offset": 0x30, "way": "i2c", "mask": 0x04},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 13, "addr": 0x0d, "offset": 0x3d, "way": "i2c"},
            "led_attrs": {
                "green": 0x04, "red": 0x02, "amber": 0x06, "default": 0x04,
                "flash": 0xff, "light": 0xff, "off": 0xff
            },
            "Rotor": {
                "Rotor1_config": {"name": "Rotor1",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                  "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 13, "addr": 0x0d, "offset": 0x16, "way": "i2c"},
                                  "Running": {"bus": 13, "addr": 0x0d, "offset": 0x31, "way": "i2c", "mask": 0x04, "is_runing": 0x04},
                                  "HwAlarm": {"bus": 13, "addr": 0x0d, "offset": 0x31, "way": "i2c", "mask": 0x04, "no_alarm": 0x04},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/13-000d/fan6_1_real_speed", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.FRONT_FAN_SPEED_MAX,
                                      "Unit": Unit.Speed,
                                  },
                                  },
                "Rotor2_config": {"name": "Rotor2",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                          "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 13, "addr": 0x0d, "offset": 0x16, "way": "i2c"},
                                  "Running": {"bus": 13, "addr": 0x0d, "offset": 0x34, "way": "i2c", "mask": 0x04, "is_runing": 0x04},
                                  "HwAlarm": {"bus": 13, "addr": 0x0d, "offset": 0x34, "way": "i2c", "mask": 0x04, "no_alarm": 0x04},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/13-000d/fan6_2_real_speed", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.REAR_FAN_SPEED_MAX,
                                      "Unit": Unit.Speed,
                                  },
                                  },
            },
        },
    ],
    "cplds": [
        {
            "name": "CPU_CPLD",
            "cpld_id": "CPLD1",
            "VersionFile": {"loc": "/dev/cpld0", "offset": 0, "len": 4, "way": "devfile_ascii"},
            "desc": "Used for system power",
            "slot": 0,
        },
        {
            "name": "MAC_CPLD_B",
            "cpld_id": "CPLD2",
            "VersionFile": {"loc": "/dev/cpld1", "offset": 0, "len": 4, "way": "devfile_ascii"},
            "desc": "Used for base functions",
            "slot": 0,
        },
        {
            "name": "MAC_CPLD_A",
            "cpld_id": "CPLD3",
            "VersionFile": {"loc": "/dev/cpld2", "offset": 0, "len": 4, "way": "devfile_ascii"},
            "desc": "Used for base functions",
            "slot": 0,
        },
        {
            "name": "FAN_CPLD_A",
            "cpld_id": "CPLD4",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/14-000d/cpld_version", "way": "sysfs"},
            "desc": "Used for system LEDs and FANs",
            "slot": 0,
        },
        {
            "name": "FAN_CPLD_B",
            "cpld_id": "CPLD5",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/13-000d/cpld_version", "way": "sysfs"},
            "desc": "Used for system LEDs and FANs",
            "slot": 0,
        },
        {
            "name": "LC1_CPLD_2",
            "cpld_id": "CPLD6",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/3-0031/cpld_version", "way": "sysfs"},
            "desc": "Used for SFP+ modules",
            "slot": 1,
        },
        {
            "name": "LC1_CPLD_1",
            "cpld_id": "CPLD7",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/3-0030/cpld_version", "way": "sysfs"},
            "desc": "Used for SFP+ modules",
            "slot": 1,
        },
        {
            "name": "LC2_CPLD_2",
            "cpld_id": "CPLD8",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/4-0031/cpld_version", "way": "sysfs"},
            "desc": "Used for SFP+ modules",
            "slot": 2,
        },
        {
            "name": "LC2_CPLD_1",
            "cpld_id": "CPLD9",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/4-0030/cpld_version", "way": "sysfs"},
            "desc": "Used for SFP+ modules",
            "slot": 2,
        },
        {
            "name": "LC3_CPLD_2",
            "cpld_id": "CPLD10",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/5-0031/cpld_version", "way": "sysfs"},
            "desc": "Used for SFP+ modules",
            "slot": 3,
        },
        {
            "name": "LC3_CPLD_1",
            "cpld_id": "CPLD11",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/5-0030/cpld_version", "way": "sysfs"},
            "desc": "Used for SFP+ modules",
            "slot": 3,
        },
        {
            "name": "LC4_CPLD_2",
            "cpld_id": "CPLD12",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/6-0031/cpld_version", "way": "sysfs"},
            "desc": "Used for SFP+ modules",
            "slot": 4,
        },
        {
            "name": "LC4_CPLD_1",
            "cpld_id": "CPLD13",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/6-0030/cpld_version", "way": "sysfs"},
            "desc": "Used for SFP+ modules",
            "slot": 4,
        },
    ],
    "dcdc": [
    ],
    "cpu": [
        {
            "name": "cpu",
            "CpuResetCntReg": {"io_addr": 0xb88, "way": "io"},
        }
    ],
    "sfps": {
        "ver": '1.0',
        "port_index_start": 0,
        "port_num": 128,
        "log_level": 2,
        "eeprom_retry_times": 5,
        "eeprom_retry_break_sec": 0.2,
        "presence_cpld": {
            "dev_id": {
                6: {
                    "offset": {
                        0x10: "1-8",
                        0x11: "9-16",
                    },
                },
                5: {
                    "offset": {
                        0x10: "17-24",
                        0x11: "25-32",
                    },
                },
                8: {
                    "offset": {
                        0x10: "33-40",
                        0x11: "41-48",
                    },
                },
                7: {
                    "offset": {
                        0x10: "49-56",
                        0x11: "57-64",
                    },
                },
                10: {
                    "offset": {
                        0x10: "65-72",
                        0x11: "73-80",
                    },
                },
                9: {
                    "offset": {
                        0x10: "81-88",
                        0x11: "89-96",
                    },
                },
                12: {
                    "offset": {
                        0x10: "97-104",
                        0x11: "105-112",
                    },
                },
                11: {
                    "offset": {
                        0x10: "113-120",
                        0x11: "121-128",
                    },
                },
            },
        },
        "presence_val_is_present": 0,
        "eeprom_path": "/sys/bus/i2c/devices/i2c-%d/%d-0050/eeprom",
        "eeprom_path_key": list(range(71, 199)),
        "optoe_driver_path": "/sys/bus/i2c/devices/i2c-%d/%d-0050/dev_class",
        "optoe_driver_key": list(range(71, 199)),
        "reset_cpld": {
            "dev_id": {
                6: {
                    "offset": {
                        0x14: "1-8",
                        0x15: "9-16",
                    },
                },
                5: {
                    "offset": {
                        0x14: "17-24",
                        0x15: "25-32",
                    },
                },
                8: {
                    "offset": {
                        0x14: "33-40",
                        0x15: "41-48",
                    },
                },
                7: {
                    "offset": {
                        0x14: "49-56",
                        0x15: "57-64",
                    },
                },
                10: {
                    "offset": {
                        0x14: "65-72",
                        0x15: "73-80",
                    },
                },
                9: {
                    "offset": {
                        0x14: "81-88",
                        0x15: "89-96",
                    },
                },
                12: {
                    "offset": {
                        0x14: "97-104",
                        0x15: "105-112",
                    },
                },
                11: {
                    "offset": {
                        0x14: "113-120",
                        0x15: "121-128",
                    },
                },
            }
        },
        "reset_val_is_reset": 0,
    }
}
