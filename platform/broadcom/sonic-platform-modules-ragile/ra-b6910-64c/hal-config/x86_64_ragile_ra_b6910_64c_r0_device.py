#!/usr/bin/python3

psu_fan_airflow = {
    "F2B": ['CSU800AP-3-300', 'GW-CRPS800N2C'],
    "B2F": []
}

fanairflow = {
    "F2B": ['M6520-FAN-F'],
    "B2F": [],
}

psu_display_name = {
    "PA800I-F": ['GW-CRPS800N2C', 'CSU800AP-3-300'],
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


PSU_NOT_PRESENT_PWM = 100


class threshold:
    PSU_TEMP_MIN = -10 * 1000
    PSU_TEMP_MAX = 60 * 1000

    PSU_FAN_SPEED_MIN = 150
    PSU_FAN_SPEED_MAX = 12000

    PSU_FAN_SPEED_TOLERANCE = 40

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

    FAN_SPEED_MAX = 10000
    FAN_SPEED_MIN = 750

    FAN_SPEED_TOLERANCE = 30


class Description:
    CPLD = "Used for managing IO modules, SFP+ modules and system LEDs"
    BIOS = "Performs initialization of hardware components during booting"
    FPGA = "Platform management controller for on-board temperature monitoring, in-chassis power"


devices = {
    "onie_e2": [
        {
            "name": "ONIE_E2",
            "e2loc": {"loc": "/sys/bus/i2c/devices/2-0057/eeprom", "way": "sysfs"},
        },
    ],
    "psus": [
        {
            "e2loc": {"loc": "/sys/bus/i2c/devices/7-0050/eeprom", "way": "sysfs"},
            "pmbusloc": {"bus": 7, "addr": 0x58, "way": "i2c"},
            "present": {"bus": 2, "addr": 0x37, "offset": 0x51, "way": "i2c", "mask": 0x01},
            "name": "PSU1",
            "psu_display_name": psu_display_name,
            "airflow": psu_fan_airflow,
            "psu_not_present_pwm": PSU_NOT_PRESENT_PWM,
            "psu_fan_tolerance": threshold.PSU_FAN_SPEED_TOLERANCE,
            "TempStatus": {"bus": 7, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x0004},
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-7/7-0058/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": threshold.PSU_TEMP_MIN,
                "Max": threshold.PSU_TEMP_MAX,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            },
            "FanStatus": {"bus": 7, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x0400},
            "FanSpeed": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-7/7-0058/hwmon/hwmon*/fan1_input", "way": "sysfs"},
                "Min": threshold.PSU_FAN_SPEED_MIN,
                "Max": threshold.PSU_FAN_SPEED_MAX,
                "Unit": Unit.Speed
            },
            "InputsStatus": {"bus": 7, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x2000},
            "InputsType": {"bus": 7, "addr": 0x58, "offset": 0x80, "way": "i2c", 'psutypedecode': psutypedecode},
            "InputsVoltage": {
                'AC': {
                    "value": {"loc": "/sys/bus/i2c/devices/i2c-7/7-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_AC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_AC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'DC': {
                    "value": {"loc": "/sys/bus/i2c/devices/i2c-7/7-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_DC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_DC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'other': {
                    "value": {"loc": "/sys/bus/i2c/devices/i2c-7/7-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.ERR_VALUE,
                    "Max": threshold.ERR_VALUE,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                }
            },
            "InputsCurrent":
            {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-7/7-0058/hwmon/hwmon*/curr1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_CURRENT_MIN,
                "Max": threshold.PSU_INPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "InputsPower":
            {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-7/7-0058/hwmon/hwmon*/power1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_POWER_MIN,
                "Max": threshold.PSU_INPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
            "OutputsStatus": {"bus": 7, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x8800},
            "OutputsVoltage":
            {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-7/7-0058/hwmon/hwmon*/in2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_VOLTAGE_MIN,
                "Max": threshold.PSU_OUTPUT_VOLTAGE_MAX,
                "Unit": Unit.Voltage,
                "format": "float(float(%s)/1000)"
            },
            "OutputsCurrent":
            {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-7/7-0058/hwmon/hwmon*/curr2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_CURRENT_MIN,
                "Max": threshold.PSU_OUTPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "OutputsPower":
            {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-7/7-0058/hwmon/hwmon*/power2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_POWER_MIN,
                "Max": threshold.PSU_OUTPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
        },
        {
            "e2loc": {"loc": "/sys/bus/i2c/devices/8-0053/eeprom", "way": "sysfs"},
            "pmbusloc": {"bus": 8, "addr": 0x5b, "way": "i2c"},
            "present": {"bus": 2, "addr": 0x37, "offset": 0x51, "way": "i2c", "mask": 0x10},
            "name": "PSU2",
            "psu_display_name": psu_display_name,
            "airflow": psu_fan_airflow,
            "psu_not_present_pwm": PSU_NOT_PRESENT_PWM,
            "psu_fan_tolerance": threshold.PSU_FAN_SPEED_TOLERANCE,
            "TempStatus": {"bus": 8, "addr": 0x5b, "offset": 0x79, "way": "i2cword", "mask": 0x0004},
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-8/8-005b/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": threshold.PSU_TEMP_MIN,
                "Max": threshold.PSU_TEMP_MAX,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            },
            "FanStatus": {"bus": 8, "addr": 0x5b, "offset": 0x79, "way": "i2cword", "mask": 0x0400},
            "FanSpeed": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-8/8-005b/hwmon/hwmon*/fan1_input", "way": "sysfs"},
                "Min": threshold.PSU_FAN_SPEED_MIN,
                "Max": threshold.PSU_FAN_SPEED_MAX,
                "Unit": Unit.Speed
            },
            "InputsStatus": {"bus": 8, "addr": 0x5b, "offset": 0x79, "way": "i2cword", "mask": 0x2000},
            "InputsType": {"bus": 8, "addr": 0x5b, "offset": 0x80, "way": "i2c", 'psutypedecode': psutypedecode},
            "InputsVoltage": {
                'AC': {
                    "value": {"loc": "/sys/bus/i2c/devices/i2c-8/8-005b/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_AC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_AC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'DC': {
                    "value": {"loc": "/sys/bus/i2c/devices/i2c-8/8-005b/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_DC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_DC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'other': {
                    "value": {"loc": "/sys/bus/i2c/devices/i2c-8/8-005b/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.ERR_VALUE,
                    "Max": threshold.ERR_VALUE,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                }
            },
            "InputsCurrent":
            {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-8/8-005b/hwmon/hwmon*/curr1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_CURRENT_MIN,
                "Max": threshold.PSU_INPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "InputsPower":
            {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-8/8-005b/hwmon/hwmon*/power1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_POWER_MIN,
                "Max": threshold.PSU_INPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
            "OutputsStatus": {"bus": 8, "addr": 0x5b, "offset": 0x79, "way": "i2cword", "mask": 0x8800},
            "OutputsVoltage":
            {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-8/8-005b/hwmon/hwmon*/in2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_VOLTAGE_MIN,
                "Max": threshold.PSU_OUTPUT_VOLTAGE_MAX,
                "Unit": Unit.Voltage,
                "format": "float(float(%s)/1000)"
            },
            "OutputsCurrent":
            {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-8/8-005b/hwmon/hwmon*/curr2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_CURRENT_MIN,
                "Max": threshold.PSU_OUTPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "OutputsPower":
            {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-8/8-005b/hwmon/hwmon*/power2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_POWER_MIN,
                "Max": threshold.PSU_OUTPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
        }
    ],
    "temps": [
        {
            "name": "BOARD_TEMP",
            "temp_id": "TEMP1",
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/2-004a/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": -10000,
                "Low": 0,
                "High": 70000,
                "Max": 75000,
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
                "High": 95000,
                "Max": 103000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
        {
            "name": "INLET_TEMP",
            "temp_id": "TEMP3",
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/2-0048/hwmon/hwmon*/temp1_input", "way": "sysfs"},
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
                "value": {"loc": "/sys/bus/i2c/devices/2-0049/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": -10000,
                "Low": 0,
                "High": 50000,
                "Max": 60000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
        {
            "name": "SWITCH_TEMP",
            "temp_id": "TEMP5",
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/2-004a/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": 2000,
                "Low": 10000,
                "High": 95000,
                "Max": 103000,
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
            "name": "FRONT_SYS_LED",
            "led_type": "SYS_LED",
            "led": {"bus": 2, "addr": 0x33, "offset": 0xb2, "way": "i2c"},
            "led_attrs": {
                "green": 0x01, "red": 0x02, "amber": 0x03, "default": 0x01,
                "flash": 0xff, "light": 0xff, "off": 0, "mask": 0xff
            },
        },
        {
            "name": "FRONT_PSU_LED",
            "led_type": "PSU_LED",
            "led": {"bus": 2, "addr": 0x33, "offset": 0xb3, "way": "i2c"},
            "led_attrs": {
                "green": 0x04, "red": 0x02, "amber": 0x06, "default": 0x04,
                "flash": 0xff, "light": 0xff, "off": 0, "mask": 0xff
            },
        },
        {
            "name": "FRONT_FAN_LED",
            "led_type": "FAN_LED",
            "led": {"bus": 2, "addr": 0x33, "offset": 0xb4, "way": "i2c"},
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
            "e2loc": {"loc": "/sys/bus/i2c/devices/3-0053/eeprom", "way": "sysfs"},
            "present": {"bus": 2, "addr": 0x37, "offset": 0x30, "way": "i2c", "mask": 0x01},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FAN_SPEED_MAX,
            "led": {"bus": 2, "addr": 0x32, "offset": 0x23, "way": "i2c"},
            "led_attrs": {
                "green": 0x09, "red": 0x0a, "amber": 0x03, "default": 0xf5,
                "flash": 0xff, "light": 0xff, "off": 0xfb
            },
            "Rotor": {
                "Rotor1_config": {"name": "Rotor1",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                  "SpeedMax": threshold.FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 2, "addr": 0x32, "offset": 0x15, "way": "i2c"},
                                  "Running": {"bus": 2, "addr": 0x37, "offset": 0x31, "way": "i2c", "mask": 0x01, "is_runing": 0x01},
                                  "HwAlarm": {"bus": 2, "addr": 0x37, "offset": 0x31, "way": "i2c", "mask": 0x01, "no_alarm": 0x01},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/2-0037/hwmon/hwmon*/fan1_input", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.FAN_SPEED_MAX,
                                      "tolerance": threshold.FAN_SPEED_TOLERANCE,
                                      "Unit": Unit.Speed,
                                  },
                                  },
            },
        },
        {
            "name": "FAN2",
            "airflow": fanairflow,
            "e2loc": {"loc": "/sys/bus/i2c/devices/4-0053/eeprom", "way": "sysfs"},
            "present": {"bus": 2, "addr": 0x37, "offset": 0x30, "way": "i2c", "mask": 0x02},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FAN_SPEED_MAX,
            "led": {"bus": 2, "addr": 0x32, "offset": 0x24, "way": "i2c"},
            "led_attrs": {
                "green": 0x09, "red": 0x0a, "amber": 0x03, "default": 0xf5,
                "flash": 0xff, "light": 0xff, "off": 0xfb
            },
            "Rotor": {
                "Rotor1_config": {"name": "Rotor1",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                  "SpeedMax": threshold.FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 2, "addr": 0x32, "offset": 0x15, "way": "i2c"},
                                  "Running": {"bus": 2, "addr": 0x37, "offset": 0x31, "way": "i2c", "mask": 0x02, "is_runing": 0x02},
                                  "HwAlarm": {"bus": 2, "addr": 0x37, "offset": 0x31, "way": "i2c", "mask": 0x02, "no_alarm": 0x02},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/2-0037/hwmon/hwmon*/fan2_input", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.FAN_SPEED_MAX,
                                      "tolerance": threshold.FAN_SPEED_TOLERANCE,
                                      "Unit": Unit.Speed,
                                  },
                                  },
            },
        },
        {
            "name": "FAN3",
            "airflow": fanairflow,
            "e2loc": {"loc": "/sys/bus/i2c/devices/5-0053/eeprom", "way": "sysfs"},
            "present": {"bus": 2, "addr": 0x37, "offset": 0x30, "way": "i2c", "mask": 0x04},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FAN_SPEED_MAX,
            "led": {"bus": 2, "addr": 0x32, "offset": 0x25, "way": "i2c"},
            "led_attrs": {
                "green": 0x09, "red": 0x0a, "amber": 0x03, "default": 0xf5,
                "flash": 0xff, "light": 0xff, "off": 0xfb
            },
            "Rotor": {
                "Rotor1_config": {"name": "Rotor1",
                                          "SpeedMin": threshold.FAN_SPEED_MIN,
                                  "SpeedMax": threshold.FAN_SPEED_MAX,
                                  "Set_speed": {"bus": 2, "addr": 0x32, "offset": 0x15, "way": "i2c"},
                                  "Running": {"bus": 2, "addr": 0x37, "offset": 0x31, "way": "i2c", "mask": 0x04, "is_runing": 0x04},
                                  "HwAlarm": {"bus": 2, "addr": 0x37, "offset": 0x31, "way": "i2c", "mask": 0x04, "no_alarm": 0x04},
                                  "Speed": {
                                      "value": {"loc": "/sys/bus/i2c/devices/2-0037/hwmon/hwmon*/fan3_input", "way": "sysfs"},
                                      "Min": threshold.FAN_SPEED_MIN,
                                      "Max": threshold.FAN_SPEED_MAX,
                                      "tolerance": threshold.FAN_SPEED_TOLERANCE,
                                      "Unit": Unit.Speed,
                                  },
                                  },
            },
        },

    ],
    "cplds": [
        {
            "name": "MAC_CPLDA",
            "cpld_id": "CPLD1",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/2-0033/cpld_version", "way": "sysfs"},
            "desc": "Used for SFP+ modules",
            "slot": 0,
        },
        {
            "name": "MAC_CPLDB",
            "cpld_id": "CPLD2",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/2-0035/cpld_version", "way": "sysfs"},
            "desc": "Used for SFP+ modules",
            "slot": 0,
        },
        {
            "name": "CONNECT_CPLDA",
            "cpld_id": "CPLD3",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/2-0037/cpld_version", "way": "sysfs"},
            "desc": "Used for system LEDs and FANs",
            "slot": 0,
        },
        {
            "name": "CPU_CPLD",
            "cpld_id": "CPLD4",
            "VersionFile": {"loc": "/sys/bus/i2c/devices/0-000d/cpld_version", "way": "sysfs"},
            "desc": "Used for system power",
            "slot": 1,
        },
    ],
    "dcdc": [
        {
            "name": "SYS_1.8V",
            "dcdc_id": "DCDC1",
            "value": {
                "loc": "/sys/bus/i2c/devices/2-0033/hwmon/*/in7_input",
                "way": "sysfs",
            },
            "read_times": 11,
            "Min": 1500,
            "Low": 1600,
            "High": 2000,
            "Max": 2100,
            "Unit": "V",
            "format": "float(float(%s)/1000)",
        },
        {
            "name": "SYS_1.2V",
            "dcdc_id": "DCDC2",
            "value": {
                "loc": "/sys/bus/i2c/devices/2-0033/hwmon/*/in2_input",
                "way": "sysfs",
            },
            "read_times": 11,
            "Min": 1000,
            "Low": 1100,
            "High": 1300,
            "Max": 1400,
            "Unit": "V",
            "format": "float(float(%s)/1000)",
        },
        {
            "name": "SWITCH_VCORE",
            "dcdc_id": "DCDC3",
            "value": {
                "loc": "/sys/bus/i2c/devices/2-0060/hwmon/*/in2_input",
                "way": "sysfs",
            },
            "read_times": 11,
            "Min": 600,
            "Low": 650,
            "High": 1100,
            "Max": 1200,
            "Unit": "V",
            "format": "float(float(%s)/1000)",
        },
    ],
    "cpu": [
        {
            "name": "cpu",
            "CpuResetCntReg": {"bus": 1, "addr": 0x36, "offset": 0xa1, "way": "i2c"},
        }
    ],
    "sfps": {
        "ver": '1.0',
        "port_index_start": 0,
        "port_num": 64,
        "log_level": 2,
        "eeprom_retry_times": 5,
        "eeprom_retry_break_sec": 0.2,
        "presence_cpld": {
            "dev_id": {
                5: {
                    "offset": {
                        0x30: "1-8",
                        0x31: "9-16",
                        0x32: "33-40",
                        0x33: "41-48",
                    },
                },
                6: {
                    "offset": {
                        0x30: "17-24",
                        0x31: "25-32",
                        0x32: "49-56",
                        0x33: "57-64",
                    },
                },
            },
        },
        "presence_val_is_present": 0,
        "eeprom_path": "/sys/bus/i2c/devices/i2c-%d/%d-0050/eeprom",
        "eeprom_path_key": list(range(11, 75)),
        "optoe_driver_path": "/sys/bus/i2c/devices/i2c-%d/%d-0050/dev_class",
        "optoe_driver_key": list(range(11, 75)),
        "reset_cpld": {
            "dev_id": {
                5: {
                    "offset": {
                        0xb9: "1-8",
                        0xba: "9-16",
                        0xbb: "33-40",
                        0xbc: "41-48",
                    },
                },
                6: {
                    "offset": {
                        0xb9: "17-24",
                        0xba: "25-32",
                        0xbb: "49-56",
                        0xbc: "57-64",
                    },
                },
            }
        },
        "reset_val_is_reset": 0,
    }
}
