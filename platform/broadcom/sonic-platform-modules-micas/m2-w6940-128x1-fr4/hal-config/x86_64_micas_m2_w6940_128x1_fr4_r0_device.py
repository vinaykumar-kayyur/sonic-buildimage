#!/usr/bin/python3

psu_fan_airflow = {
    "intake": ['DLK3000AN12C31', 'CRPS3000CL'],
    "exhaust": []
}

fanairflow = {
    "intake": ['M2EFAN V-F'],
    "exhaust": [],
}

psu_display_name = {
    "PA3000I-F": ['DLK3000AN12C31', 'CRPS3000CL'],
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
    PSU_TEMP_MIN = -5 * 1000
    PSU_TEMP_MAX = 55 * 1000

    PSU_FAN_SPEED_MIN = 3500
    PSU_FAN_SPEED_MAX = 23500

    PSU_OUTPUT_VOLTAGE_MIN = 11 * 1000
    PSU_OUTPUT_VOLTAGE_MAX = 13 * 1000

    PSU_AC_INPUT_VOLTAGE_MIN = 90 * 1000
    PSU_AC_INPUT_VOLTAGE_MAX = 264 * 1000

    PSU_DC_INPUT_VOLTAGE_MIN = 180 * 1000
    PSU_DC_INPUT_VOLTAGE_MAX = 320 * 1000

    ERR_VALUE = -9999999

    PSU_OUTPUT_POWER_MIN = 0 * 1000 * 1000
    PSU_OUTPUT_POWER_MAX = 3000 * 1000 * 1000

    PSU_INPUT_POWER_MIN = 0 * 1000 * 1000
    PSU_INPUT_POWER_MAX = 3100 * 1000 * 1000

    PSU_OUTPUT_CURRENT_MIN = 0 * 1000
    PSU_OUTPUT_CURRENT_MAX = 246 * 1000

    PSU_INPUT_CURRENT_MIN = 0 * 1000
    PSU_INPUT_CURRENT_MAX = 20 * 1000

    FRONT_FAN_SPEED_MAX = 13530
    REAR_FAN_SPEED_MAX = 11770
    FAN_SPEED_MIN = 2000

devices = {
    "onie_e2": [
        {
            "name": "ONIE_E2",
            "e2loc": {"loc": "/sys/bus/i2c/devices/1-0056/eeprom", "way": "sysfs"},
            "airflow": "intake"
        },
    ],
    "psus": [
        {
            "e2loc": {"loc": "/sys/bus/i2c/devices/11-0050/eeprom", "way": "sysfs"},
            "pmbusloc": {"bus": 11, "addr": 0x58, "way": "i2c"},
            "present": {"loc": "/sys/wb_plat/psu/psu1/present", "way": "sysfs", "mask": 0x01, "okval": 1},
            "name": "PSU1",
            "psu_display_name": psu_display_name,
            "psu_display_name": psu_display_name,
            "airflow": psu_fan_airflow,
            "TempStatus": {"bus": 11, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x0004},
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-11/11-0058/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": threshold.PSU_TEMP_MIN,
                "Max": threshold.PSU_TEMP_MAX,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            },
            "FanStatus": {"bus": 11, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x0400},
            "FanSpeed": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-11/11-0058/hwmon/hwmon*/fan1_input", "way": "sysfs"},
                "Min": threshold.PSU_FAN_SPEED_MIN,
                "Max": threshold.PSU_FAN_SPEED_MAX,
                "Unit": Unit.Speed
            },
            "psu_fan_tolerance": 40,
            "InputsStatus": {"bus": 11, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x2000},
            "InputsType": {"bus": 11, "addr": 0x58, "offset": 0x80, "way": "i2c", 'psutypedecode': psutypedecode},
            "InputsVoltage": {
                'AC': {
                    "value": {"loc": "/sys/bus/i2c/devices/i2c-11/11-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_AC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_AC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"

                },
                'DC': {
                    "value": {"loc": "/sys/bus/i2c/devices/i2c-11/11-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_DC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_DC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'other': {
                    "value": {"loc": "/sys/bus/i2c/devices/i2c-11/11-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.ERR_VALUE,
                    "Max": threshold.ERR_VALUE,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                }
            },
            "InputsCurrent": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-11/11-0058/hwmon/hwmon*/curr1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_CURRENT_MIN,
                "Max": threshold.PSU_INPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "InputsPower": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-11/11-0058/hwmon/hwmon*/power1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_POWER_MIN,
                "Max": threshold.PSU_INPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
            "OutputsStatus": {"bus": 11, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x8800},
            "OutputsVoltage": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-11/11-0058/hwmon/hwmon*/in2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_VOLTAGE_MIN,
                "Max": threshold.PSU_OUTPUT_VOLTAGE_MAX,
                "Unit": Unit.Voltage,
                "format": "float(float(%s)/1000)"
            },
            "OutputsCurrent": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-11/11-0058/hwmon/hwmon*/curr2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_CURRENT_MIN,
                "Max": threshold.PSU_OUTPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "OutputsPower": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-11/11-0058/hwmon/hwmon*/power2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_POWER_MIN,
                "Max": threshold.PSU_OUTPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
        },
        {
            "e2loc": {"loc": "/sys/bus/i2c/devices/10-0050/eeprom", "way": "sysfs"},
            "pmbusloc": {"bus": 10, "addr": 0x58, "way": "i2c"},
            "present": {"loc": "/sys/wb_plat/psu/psu2/present", "way": "sysfs", "mask": 0x01, "okval": 1},
            "name": "PSU2",
            "psu_display_name": psu_display_name,
            "airflow": psu_fan_airflow,
            "TempStatus": {"bus": 10, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x0004},
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-10/10-0058/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": threshold.PSU_TEMP_MIN,
                "Max": threshold.PSU_TEMP_MAX,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            },
            "FanStatus": {"bus": 10, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x0400},
            "FanSpeed": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-10/10-0058/hwmon/hwmon*/fan1_input", "way": "sysfs"},
                "Min": threshold.PSU_FAN_SPEED_MIN,
                "Max": threshold.PSU_FAN_SPEED_MAX,
                "Unit": Unit.Speed
            },
            "psu_fan_tolerance": 40,
            "InputsStatus": {"bus":10, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x2000},
            "InputsType": {"bus": 10, "addr": 0x58, "offset": 0x80, "way": "i2c", 'psutypedecode': psutypedecode},
            "InputsVoltage": {
                'AC': {
                    "value": {"loc": "/sys/bus/i2c/devices/i2c-10/10-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_AC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_AC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"

                },
                'DC': {
                    "value": {"loc": "/sys/bus/i2c/devices/i2c-10/10-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.PSU_DC_INPUT_VOLTAGE_MIN,
                    "Max": threshold.PSU_DC_INPUT_VOLTAGE_MAX,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                },
                'other': {
                    "value": {"loc": "/sys/bus/i2c/devices/i2c-10/10-0058/hwmon/hwmon*/in1_input", "way": "sysfs"},
                    "Min": threshold.ERR_VALUE,
                    "Max": threshold.ERR_VALUE,
                    "Unit": Unit.Voltage,
                    "format": "float(float(%s)/1000)"
                }
            },
            "InputsCurrent": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-10/10-0058/hwmon/hwmon*/curr1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_CURRENT_MIN,
                "Max": threshold.PSU_INPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "InputsPower": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-10/10-0058/hwmon/hwmon*/power1_input", "way": "sysfs"},
                "Min": threshold.PSU_INPUT_POWER_MIN,
                "Max": threshold.PSU_INPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
            "OutputsStatus": {"bus": 10, "addr": 0x58, "offset": 0x79, "way": "i2cword", "mask": 0x8800},
            "OutputsVoltage": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-10/10-0058/hwmon/hwmon*/in2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_VOLTAGE_MIN,
                "Max": threshold.PSU_OUTPUT_VOLTAGE_MAX,
                "Unit": Unit.Voltage,
                "format": "float(float(%s)/1000)"
            },
            "OutputsCurrent": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-10/10-0058/hwmon/hwmon*/curr2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_CURRENT_MIN,
                "Max": threshold.PSU_OUTPUT_CURRENT_MAX,
                "Unit": Unit.Current,
                "format": "float(float(%s)/1000)"
            },
            "OutputsPower": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-10/10-0058/hwmon/hwmon*/power2_input", "way": "sysfs"},
                "Min": threshold.PSU_OUTPUT_POWER_MIN,
                "Max": threshold.PSU_OUTPUT_POWER_MAX,
                "Unit": Unit.Power,
                "format": "float(float(%s)/1000000)"
            },
        },
    ],
    "temps": [
        {
            "name": "CPU_TEMP",
            "temp_id": "TEMP1",
            "api_name": "CPU",
            "Temperature": {
                "value": {"loc": "/sys/bus/platform/devices/coretemp.0/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": 2000,
                "Low": 10000,
                "High": 99000,
                "Max": 104000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
        {
            "name": "INLET_TEMP",
            "temp_id": "TEMP2",
            "api_name": "Inlet",
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/35-004d/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": -10000,
                "Low": 0,
                "High": 38000,
                "Max": 45000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
        {
            "name": "OUTLET_TEMP",
            "temp_id": "TEMP3",
            "api_name": "Outlet",
            "Temperature": {
                "value": [
                    {"loc": "/sys/bus/i2c/devices/8-0048/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/8-0049/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/9-0048/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                    {"loc": "/sys/bus/i2c/devices/9-004d/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                ],
                "Min": -10000,
                "Low": 0,
                "High": 70000,
                "Max": 80000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
        {
            "name": "SWITCH_TEMP",
            "temp_id": "TEMP4",
            "api_name": "ASIC_TEMP",
            "Temperature": {
                "value": {"loc": "/sys/wb_plat/sensor/temp2/temp_input", "way": "sysfs"},
                "Min": 2000,
                "Low": 10000,
                "High": 100000,
                "Max": 105000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
        {
            "name": "PSU1_TEMP",
            "temp_id": "TEMP5",
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-11/11-0058/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": -10000,
                "Low": 0,
                "High": 55000,
                "Max": 60000,
                "Unit": Unit.Temperature,
                "format": "float(float(%s)/1000)"
            }
        },
        {
            "name": "PSU2_TEMP",
            "temp_id": "TEMP6",
            "Temperature": {
                "value": {"loc": "/sys/bus/i2c/devices/i2c-10/10-0058/hwmon/hwmon*/temp1_input", "way": "sysfs"},
                "Min": -10000,
                "Low": 0,
                "High": 55000,
                "Max": 60000,
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
            },
            "invalid": -10000,
            "error": -9999,
        }
    ],
    "leds": [
        {
            "name": "FRONT_SYS_LED",
            "led_type": "SYS_LED",
            "led": {"loc": "/dev/cpld1", "offset": 0x50, "len": 1, "way": "devfile"},
            "led_attrs": {
                "off": 0x00, "green": 0x02, "amber": 0x06, "red": 0x06, "mask": 0x07
            },
        },
        {
            "name": "FRONT_PSU_LED",
            "led_type": "PSU_LED",
            "led": {"loc": "/dev/cpld1", "offset": 0x51, "len": 1, "way": "devfile"},
            "led_attrs": {
                "off": 0x00, "green": 0x02, "amber": 0x06, "red": 0x06, "mask": 0x07
            },
        },
        {
            "name": "FRONT_FAN_LED",
            "led_type": "FAN_LED",
            "led": {"loc": "/dev/cpld1", "offset": 0x52, "len": 1, "way": "devfile"},
            "led_attrs": {
                "off": 0x00, "green": 0x02, "amber": 0x06, "red": 0x06, "mask": 0x07
            },
        },
        {
            "name": "FRONT_SMB_LED",
            "led_type": "SMB_LED",
            "led": {"loc": "/dev/cpld1", "offset": 0x53, "len": 1, "way": "devfile"},
            "led_attrs": {
                "off": 0x00, "green": 0x02, "amber": 0x06, "red": 0x06, "mask": 0x07
            },
        },
    ],
    "fans": [
        {
            "name": "FAN7",
            "airflow": fanairflow,
            "e2loc": {'loc': '/sys/bus/i2c/devices/i2c-43/43-0050/eeprom', 'offset': 0, 'len': 256, 'way': 'devfile'},
            "present": {"loc": "/sys/wb_plat/fan/fan7/present", "way": "sysfs", "mask": 0x01, "okval": 1},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 44, "addr": 0x0d, "offset": 0x60, "way": "i2c"},
            "led_attrs": {
                "off": 0x00, "green": 0x06, "amber": 0x01, "red": 0x01, "mask": 0x07
            },
            "PowerMax": 80.64,
            "Rotor": {
                "Rotor1_config": {
                    "name": "Rotor1",
                    "Set_speed": {"bus": 44, "addr": 0x0d, "offset": 0x90, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan7/motor0/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan7/motor0/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan7/motor0/speed", "way": "sysfs"},
                        "Min": threshold.FAN_SPEED_MIN,
                        "Max": threshold.FRONT_FAN_SPEED_MAX,
                        "Unit": Unit.Speed,
                    },
                },
                "Rotor2_config": {
                    "name": "Rotor2",
                    "Set_speed": {"bus": 44, "addr": 0x0d, "offset": 0x90, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan7/motor1/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan7/motor1/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan7/motor1/speed", "way": "sysfs"},
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
            "e2loc": {'loc': '/sys/bus/i2c/devices/i2c-42/42-0050/eeprom', 'offset': 0, 'len': 256, 'way': 'devfile'},
            "present": {"loc": "/sys/wb_plat/fan/fan5/present", "way": "sysfs", "mask": 0x01, "okval": 1},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 44, "addr": 0x0d, "offset": 0x61, "way": "i2c"},
            "led_attrs": {
                "off": 0x00, "green": 0x06, "amber": 0x01, "red": 0x01, "mask": 0x07
            },
            "PowerMax": 80.64,
            "Rotor": {
                "Rotor1_config": {
                    "name": "Rotor1",
                    "Set_speed": {"bus": 44, "addr": 0x0d, "offset": 0x91, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan5/motor0/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan5/motor0/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan5/motor0/speed", "way": "sysfs"},
                        "Min": threshold.FAN_SPEED_MIN,
                        "Max": threshold.FRONT_FAN_SPEED_MAX,
                        "Unit": Unit.Speed,
                    },
                },
                "Rotor2_config": {
                    "name": "Rotor2",
                    "Set_speed": {"bus": 44, "addr": 0x0d, "offset": 0x91, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan5/motor1/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan5/motor1/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan5/motor1/speed", "way": "sysfs"},
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
            "e2loc": {'loc': '/sys/bus/i2c/devices/i2c-41/41-0050/eeprom', 'offset': 0, 'len': 256, 'way': 'devfile'},
            "present": {"loc": "/sys/wb_plat/fan/fan3/present", "way": "sysfs", "mask": 0x01, "okval": 1},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 44, "addr": 0x0d, "offset": 0x62, "way": "i2c"},
            "led_attrs": {
                "off": 0x00, "green": 0x06, "amber": 0x01, "red": 0x01, "mask": 0x07
            },
            "PowerMax": 80.64,
            "Rotor": {
                "Rotor1_config": {
                    "name": "Rotor1",
                    "Set_speed": {"bus": 44, "addr": 0x0d, "offset": 0x92, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan3/motor0/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan3/motor0/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan3/motor0/speed", "way": "sysfs"},
                        "Min": threshold.FAN_SPEED_MIN,
                        "Max": threshold.FRONT_FAN_SPEED_MAX,
                        "Unit": Unit.Speed,
                    },
                },
                "Rotor2_config": {
                    "name": "Rotor2",
                    "Set_speed": {"bus": 44, "addr": 0x0d, "offset": 0x92, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan3/motor1/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan3/motor1/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan3/motor1/speed", "way": "sysfs"},
                        "Min": threshold.FAN_SPEED_MIN,
                        "Max": threshold.REAR_FAN_SPEED_MAX,
                        "Unit": Unit.Speed,
                    },
                },
            },
        },
        {
            "name": "FAN1",
            "airflow": fanairflow,
            "e2loc": {'loc': '/sys/bus/i2c/devices/i2c-40/40-0050/eeprom', 'offset': 0, 'len': 256, 'way': 'devfile'},
            "present": {"loc": "/sys/wb_plat/fan/fan1/present", "way": "sysfs", "mask": 0x01, "okval": 1},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 44, "addr": 0x0d, "offset": 0x63, "way": "i2c"},
            "led_attrs": {
                "off": 0x00, "green": 0x06, "amber": 0x01, "red": 0x01, "mask": 0x07
            },
            "PowerMax": 80.64,
            "Rotor": {
                "Rotor1_config": {
                    "name": "Rotor1",
                    "Set_speed": {"bus": 44, "addr": 0x0d, "offset": 0x93, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan1/motor0/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan1/motor0/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                     "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan1/motor0/speed", "way": "sysfs"},
                        "Min": threshold.FAN_SPEED_MIN,
                        "Max": threshold.FRONT_FAN_SPEED_MAX,
                        "Unit": Unit.Speed,
                    },
                },
                "Rotor2_config": {
                    "name": "Rotor2",
                    "Set_speed": {"bus": 44, "addr": 0x0d, "offset": 0x93, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan1/motor1/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan1/motor1/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan1/motor1/speed", "way": "sysfs"},
                        "Min": threshold.FAN_SPEED_MIN,
                        "Max": threshold.REAR_FAN_SPEED_MAX,
                        "Unit": Unit.Speed,
                    },
                },
            },
        },
        {
            "name": "FAN8",
            "airflow": fanairflow,
            "e2loc": {'loc': '/sys/bus/i2c/devices/i2c-51/51-0050/eeprom', 'offset': 0, 'len': 256, 'way': 'devfile'},
            "present": {"loc": "/sys/wb_plat/fan/fan8/present", "way": "sysfs", "mask": 0x01, "okval": 1},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 52, "addr": 0x0d, "offset": 0x60, "way": "i2c"},
            "led_attrs": {
                "off": 0x00, "green": 0x06, "amber": 0x01, "red": 0x01, "mask": 0x07
            },
            "PowerMax": 80.64,
            "Rotor": {
                "Rotor1_config": {
                    "name": "Rotor1",
                    "Set_speed": {"bus": 52, "addr": 0x0d, "offset": 0x90, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan8/motor0/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan8/motor0/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan8/motor0/speed", "way": "sysfs"},
                        "Min": threshold.FAN_SPEED_MIN,
                        "Max": threshold.FRONT_FAN_SPEED_MAX,
                        "Unit": Unit.Speed,
                    },
                },
                "Rotor2_config": {
                    "name": "Rotor2",
                    "Set_speed": {"bus": 52, "addr": 0x0d, "offset": 0x90, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan8/motor1/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan8/motor1/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan8/motor1/speed", "way": "sysfs"},
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
            "e2loc": {'loc': '/sys/bus/i2c/devices/i2c-50/50-0050/eeprom', 'offset': 0, 'len': 256, 'way': 'devfile'},
            "present": {"loc": "/sys/wb_plat/fan/fan6/present", "way": "sysfs", "mask": 0x01, "okval": 1},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 52, "addr": 0x0d, "offset": 0x61, "way": "i2c"},
            "led_attrs": {
                "off": 0x00, "green": 0x06, "amber": 0x01, "red": 0x01, "mask": 0x07
            },
            "PowerMax": 80.64,
            "Rotor": {
                "Rotor1_config": {
                    "name": "Rotor1",
                    "Set_speed": {"bus": 52, "addr": 0x0d, "offset": 0x91, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan6/motor0/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan6/motor0/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan6/motor0/speed", "way": "sysfs"},
                        "Min": threshold.FAN_SPEED_MIN,
                        "Max": threshold.FRONT_FAN_SPEED_MAX,
                        "Unit": Unit.Speed,
                    },
                },
                "Rotor2_config": {
                    "name": "Rotor2",
                    "Set_speed": {"bus": 52, "addr": 0x0d, "offset": 0x91, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan6/motor1/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan6/motor1/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan6/motor1/speed", "way": "sysfs"},
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
            "e2loc": {'loc': '/sys/bus/i2c/devices/i2c-49/49-0050/eeprom', 'offset': 0, 'len': 256, 'way': 'devfile'},
            "present": {"loc": "/sys/wb_plat/fan/fan4/present", "way": "sysfs", "mask": 0x01, "okval": 1},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 52, "addr": 0x0d, "offset": 0x62, "way": "i2c"},
            "led_attrs": {
                "off": 0x00, "green": 0x06, "amber": 0x01, "red": 0x01, "mask": 0x07
            },
            "PowerMax": 80.64,
            "Rotor": {
                "Rotor1_config": {
                    "name": "Rotor1",
                    "Set_speed": {"bus": 52, "addr": 0x0d, "offset": 0x92, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan4/motor0/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan4/motor0/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan4/motor0/speed", "way": "sysfs"},
                        "Min": threshold.FAN_SPEED_MIN,
                        "Max": threshold.FRONT_FAN_SPEED_MAX,
                        "Unit": Unit.Speed,
                    },
                },
                "Rotor2_config": {
                    "name": "Rotor2",
                    "Set_speed": {"bus": 52, "addr": 0x0d, "offset": 0x92, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan4/motor1/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan4/motor1/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan4/motor1/speed", "way": "sysfs"},
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
            "e2loc": {'loc': '/sys/bus/i2c/devices/i2c-48/48-0050/eeprom', 'offset': 0, 'len': 256, 'way': 'devfile'},
            "present": {"loc": "/sys/wb_plat/fan/fan2/present", "way": "sysfs", "mask": 0x01, "okval": 1},
            "SpeedMin": threshold.FAN_SPEED_MIN,
            "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
            "led": {"bus": 52, "addr": 0x0d, "offset": 0x63, "way": "i2c"},
            "led_attrs": {
                "off": 0x00, "green": 0x06, "amber": 0x01, "red": 0x01, "mask": 0x07
            },
            "PowerMax": 80.64,
            "Rotor": {
                "Rotor1_config": {
                    "name": "Rotor1",
                    "Set_speed": {"bus": 52, "addr": 0x0d, "offset": 0x93, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan2/motor0/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan2/motor0/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.FRONT_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan2/motor0/speed", "way": "sysfs"},
                        "Min": threshold.FAN_SPEED_MIN,
                        "Max": threshold.FRONT_FAN_SPEED_MAX,
                        "Unit": Unit.Speed,
                    },
                },
                "Rotor2_config": {
                    "name": "Rotor2",
                    "Set_speed": {"bus": 52, "addr": 0x0d, "offset": 0x93, "way": "i2c"},
                    "Running": {"loc": "/sys/wb_plat/fan/fan2/motor1/status", "way": "sysfs", "mask": 0x01, "is_runing": 1},
                    "HwAlarm": {"loc": "/sys/wb_plat/fan/fan2/motor1/status", "way": "sysfs", "mask": 0x01, "no_alarm": 1},
                    "SpeedMin": threshold.FAN_SPEED_MIN,
                    "SpeedMax": threshold.REAR_FAN_SPEED_MAX,
                    "Speed": {
                        "value": {"loc": "/sys/wb_plat/fan/fan2/motor1/speed", "way": "sysfs"},
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
            "name": "CPU CPLD",
            "cpld_id": "CPLD1",
            "VersionFile": {"loc": "/dev/cpld0", "offset": 0, "len": 4, "way": "devfile_ascii"},
            "desc": "Used for system power",
            "slot": 0,
            "warm": 0,
        },
        {
            "name": "SCM CPLD",
            "cpld_id": "CPLD2",
            "VersionFile": {"loc": "/dev/cpld1", "offset": 0, "len": 4, "way": "devfile_ascii"},
            "desc": "Used for base functions",
            "slot": 0,
            "warm": 0,
        },
        {
            "name": "MCB CPLD",
            "cpld_id": "CPLD3",
            "VersionFile": {"loc": "/dev/cpld3", "offset": 0, "len": 4, "way": "devfile_ascii"},
            "desc": "Used for base functions",
            "slot": 0,
            "warm": 0,
        },
        {
            "name": "SMB CPLD",
            "cpld_id": "CPLD4",
            "VersionFile": {"loc": "/dev/cpld4", "offset": 0, "len": 4, "way": "devfile_ascii"},
            "desc": "Used for sff modules",
            "slot": 0,
            "warm": 0,
        },
        {
            "name": "FCB_T CPLD",
            "cpld_id": "CPLD5",
            "VersionFile": {"loc": "/dev/cpld5", "offset": 0, "len": 4, "way": "devfile_ascii"},
            "desc": "Used for fan modules",
            "slot": 0,
            "warm": 0,
        },
        {
            "name": "FCB_B CPLD",
            "cpld_id": "CPLD6",
            "VersionFile": {"loc": "/dev/cpld6", "offset": 0, "len": 4, "way": "devfile_ascii"},
            "desc": "Used for fan modules",
            "slot": 0,
            "warm": 0,
        },
        {
            "name": "IOB FPGA",
            "cpld_id": "CPLD7",
            "VersionFile": {"loc": "/dev/fpga0", "offset": 0, "len": 4, "way": "devfile_ascii"},
            "desc": "Used for base functions",
            "slot": 0,
            "format": "little_endian",
            "warm": 0,
        },
        {
            "name": "DOM FPGA",
            "cpld_id": "CPLD8",
            "VersionFile": {"loc": "/dev/fpga1", "offset": 0, "len": 4, "way": "devfile_ascii"},
            "desc": "Used for sff functions",
            "slot": 0,
            "format": "little_endian",
            "warm": 0,
        },
        {
            "name": "BIOS",
            "cpld_id": "CPLD9",
            "VersionFile": {"cmd": "dmidecode -s bios-version", "way": "cmd"},
            "desc": "Performs initialization of hardware components during booting",
            "slot": 0,
            "type": "str",
            "warm": 0,
        },
    ],
    "dcdc": [
        {
            "name": "SCM_53134O_V1.0_V",
            "dcdc_id": "DCDC1",
            "Min": 900,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0040/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1100,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_53134O_V1.0_C",
            "dcdc_id": "DCDC2",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0040/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_I210_V3.3_V",
            "dcdc_id": "DCDC3",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0040/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_I210_V3.3_C",
            "dcdc_id": "DCDC4",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0040/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_VDD3.3_V",
            "dcdc_id": "DCDC5",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0040/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_VDD3.3_C",
            "dcdc_id": "DCDC6",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0040/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 2200,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_VDD12.0_V",
            "dcdc_id": "DCDC7",
            "Min": 10800,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0041/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 13200,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_VDD12.0_C",
            "dcdc_id": "DCDC8",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0041/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 8800,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_OCM_V12.0_V",
            "dcdc_id": "DCDC9",
            "Min": 10800,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0041/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 13200,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_OCM_V12.0_C",
            "dcdc_id": "DCDC10",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0041/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 7700,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_SSD_V3.3_V",
            "dcdc_id": "DCDC11",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0042/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_SSD_V3.3_C",
            "dcdc_id": "DCDC12",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0042/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 1650,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_BMC_V3.3_V",
            "dcdc_id": "DCDC13",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0042/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_BMC_V3.3_C",
            "dcdc_id": "DCDC14",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0042/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 2750,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_VDD5.0_V",
            "dcdc_id": "DCDC15",
            "Min": 4500,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0042/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 5500,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SCM_VDD5.0_C",
            "dcdc_id": "DCDC16",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/33-0042/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_CORE_V",
            "dcdc_id": "DCDC17",
            "Min": 630,
            "value": {
                "loc": "/sys/bus/i2c/devices/64-0040/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 858,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_CORE_C",
            "dcdc_id": "DCDC18",
            "Min": -500,
            "value": {
                "loc": "/sys/bus/i2c/devices/64-0040/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 454850,
            "format": "float(float(%s)*2/1000)",
        },

        {
            "name": "MAC_ANALOG0 V0.9_V",
            "dcdc_id": "DCDC19",
            "Min": 810,
            "value": {
                "loc": "/sys/bus/i2c/devices/65-0040/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 990,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_ANALOG0 V0.9_C",
            "dcdc_id": "DCDC20",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/65-0040/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 77737,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_ANALOG0 V0.75_V",
            "dcdc_id": "DCDC21",
            "Min": 675,
            "value": {
                "loc": "/sys/bus/i2c/devices/65-0040/hwmon/hwmon*/in4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 825,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_ANALOG0 V0.75_C",
            "dcdc_id": "DCDC22",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/65-0040/hwmon/hwmon*/curr4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 38826,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_ANALOG1 V0.9_V",
            "dcdc_id": "DCDC23",
            "Min": 810,
            "value": {
                "loc": "/sys/bus/i2c/devices/66-0040/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 990,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_ANALOG1 V0.9_C",
            "dcdc_id": "DCDC24",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/66-0040/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 77737,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_ANALOG1 V0.75_V",
            "dcdc_id": "DCDC25",
            "Min": 675,
            "value": {
                "loc": "/sys/bus/i2c/devices/66-0040/hwmon/hwmon*/in4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 825,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_ANALOG1 V0.75_C",
            "dcdc_id": "DCDC26",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/66-0040/hwmon/hwmon*/curr4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 38826,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_PLL0_VDD0.9_V",
            "dcdc_id": "DCDC27",
            "Min": 810,
            "value": {
                "loc": "/sys/bus/i2c/devices/56-0040/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 990,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_PLL0_VDD0.9_C",
            "dcdc_id": "DCDC28",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/56-0040/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 2570,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_PLL1_VDD0.9_V",
            "dcdc_id": "DCDC29",
            "Min": 810,
            "value": {
                "loc": "/sys/bus/i2c/devices/56-0040/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 990,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_PLL1_VDD0.9_C",
            "dcdc_id": "DCDC30",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/56-0040/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 2570,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_PLL2_VDD0.9_V",
            "dcdc_id": "DCDC31",
            "Min": 810,
            "value": {
                "loc": "/sys/bus/i2c/devices/58-0040/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 990,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_PLL2_VDD0.9_C",
            "dcdc_id": "DCDC32",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/58-0040/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_PLL3_VDD0.9_V",
            "dcdc_id": "DCDC33",
            "Min": 810,
            "value": {
                "loc": "/sys/bus/i2c/devices/58-0040/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 990,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_PLL3_VDD0.9_C",
            "dcdc_id": "DCDC34",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/58-0040/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_VDD_0.8_V",
            "dcdc_id": "DCDC35",
            "Min": 720,
            "value": {
                "loc": "/sys/bus/i2c/devices/58-0040/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 880,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_VDD_0.8_C",
            "dcdc_id": "DCDC36",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/58-0040/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 1500,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_VDD_1.8_V",
            "dcdc_id": "DCDC37",
            "Min": 1620,
            "value": {
                "loc": "/sys/bus/i2c/devices/60-0040/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1980,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_VDD_1.8_C",
            "dcdc_id": "DCDC38",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/60-0040/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 2570,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_VDD_1.5_V",
            "dcdc_id": "DCDC39",
            "Min": 1350,
            "value": {
                "loc": "/sys/bus/i2c/devices/60-0040/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1650,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_VDD_1.5_C",
            "dcdc_id": "DCDC40",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/60-0040/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 1485,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_VDD_1.2_V",
            "dcdc_id": "DCDC41",
            "Min": 1080,
            "value": {
                "loc": "/sys/bus/i2c/devices/61-0040/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1320,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MAC_VDD_1.2_C",
            "dcdc_id": "DCDC42",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/61-0040/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 1600,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_AVDD_0.75_V",
            "dcdc_id": "DCDC43",
            "Min": 675,
            "value": {
                "loc": "/sys/bus/i2c/devices/69-0040/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 825,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_AVDD_0.75_C",
            "dcdc_id": "DCDC44",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/69-0040/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 88000,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_AVDD_1.2_V",
            "dcdc_id": "DCDC45",
            "Min": 1080,
            "value": {
                "loc": "/sys/bus/i2c/devices/69-0040/hwmon/hwmon*/in4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1320,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_AVDD_1.2_C",
            "dcdc_id": "DCDC46",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/69-0040/hwmon/hwmon*/curr4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 72000,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_AVDD_TX_1.8_V",
            "dcdc_id": "DCDC47",
            "Min": 1620,
            "value": {
                "loc": "/sys/bus/i2c/devices/70-0068/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1980,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_AVDD_TX_1.8_C",
            "dcdc_id": "DCDC48",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/70-0068/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 42000,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_AVDD_RX_1.8_V",
            "dcdc_id": "DCDC49",
            "Min": 1620,
            "value": {
                "loc": "/sys/bus/i2c/devices/70-0068/hwmon/hwmon*/in4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1980,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_AVDD_RX_1.8_C",
            "dcdc_id": "DCDC50",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/70-0068/hwmon/hwmon*/curr4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 4000,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_HCSL_PLL_VDD0_0.75_V",
            "dcdc_id": "DCDC51",
            "Min": 675,
            "value": {
                "loc": "/sys/bus/i2c/devices/56-0040/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 825,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_HCSL_PLL_VDD0_0.75_C",
            "dcdc_id": "DCDC52",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/56-0040/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_HCSL_PLL_VDD1_0.75_V",
            "dcdc_id": "DCDC53",
            "Min": 675,
            "value": {
                "loc": "/sys/bus/i2c/devices/57-0040/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 825,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_HCSL_PLL_VDD1_0.75_C",
            "dcdc_id": "DCDC54",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/57-0040/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_AVDD_3.3_V",
            "dcdc_id": "DCDC55",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/59-0040/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_AVDD_3.3_C",
            "dcdc_id": "DCDC56",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/59-0040/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 1100,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_VDD_HCSL_PLL_1.8_V",
            "dcdc_id": "DCDC57",
            "Min": 1620,
            "value": {
                "loc": "/sys/bus/i2c/devices/59-0040/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1980,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_VDD_HCSL_PLL_1.8_C",
            "dcdc_id": "DCDC58",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/59-0040/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_VDD_1.8_V",
            "dcdc_id": "DCDC59",
            "Min": 1620,
            "value": {
                "loc": "/sys/bus/i2c/devices/60-0040/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1980,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OE_VDD_1.8_C",
            "dcdc_id": "DCDC60",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/60-0040/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "RLML_VDD V3.3_V",
            "dcdc_id": "DCDC61",
            "Min": 1980,
            "value": {
                "loc": "/sys/bus/i2c/devices/71-0068/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 2420,
            "format": "float(float(%s)*1.5/1000)",
        },

        {
            "name": "RLML_VDD V3.3_C",
            "dcdc_id": "DCDC62",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/71-0068/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 1320,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "RLMH_VDD V3.3_V",
            "dcdc_id": "DCDC63",
            "Min": 1980,
            "value": {
                "loc": "/sys/bus/i2c/devices/71-0068/hwmon/hwmon*/in4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 2420,
            "format": "float(float(%s)*1.5/1000)",
        },

        {
            "name": "RLMH_VDD V3.3_C",
            "dcdc_id": "DCDC64",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/71-0068/hwmon/hwmon*/curr4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 1320,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_CLK_VDD3.3_V",
            "dcdc_id": "DCDC65",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/56-0041/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_CLK_VDD3.3_C",
            "dcdc_id": "DCDC66",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/56-0041/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 1100,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_CLK2_VDD1.8_V",
            "dcdc_id": "DCDC67",
            "Min": 1620,
            "value": {
                "loc": "/sys/bus/i2c/devices/56-0041/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1980,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_CLK2_VDD1.8_C",
            "dcdc_id": "DCDC68",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/56-0041/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 1100,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_CLK_VDD1.8_V",
            "dcdc_id": "DCDC69",
            "Min": 1620,
            "value": {
                "loc": "/sys/bus/i2c/devices/56-0041/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1980,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_CLK_VDD1.8_C",
            "dcdc_id": "DCDC70",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/56-0041/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 1100,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_FPGA_VDD1.8_V",
            "dcdc_id": "DCDC71",
            "Min": 1620,
            "value": {
                "loc": "/sys/bus/i2c/devices/57-0040/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1980,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_FPGA_VDD1.8_C",
            "dcdc_id": "DCDC72",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/57-0040/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_VDD_5.0_V",
            "dcdc_id": "DCDC73",
            "Min": 4500,
            "value": {
                "loc": "/sys/bus/i2c/devices/61-0040/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 5500,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_VDD_5.0_C",
            "dcdc_id": "DCDC74",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/61-0040/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 3300,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_FPGA_V3.3_V",
            "dcdc_id": "DCDC75",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/62-0040/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_FPGA_V3.3_C",
            "dcdc_id": "DCDC76",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/62-0040/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_FPGA_V1.0_V",
            "dcdc_id": "DCDC77",
            "Min": 900,
            "value": {
                "loc": "/sys/bus/i2c/devices/62-0040/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1100,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_FPGA_V1.0_C",
            "dcdc_id": "DCDC78",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/62-0040/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 1188,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_FPGA_V1.2_V",
            "dcdc_id": "DCDC79",
            "Min": 1080,
            "value": {
                "loc": "/sys/bus/i2c/devices/62-0040/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1320,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_FPGA_V1.2_C",
            "dcdc_id": "DCDC80",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/62-0040/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_VDD_3.3_V",
            "dcdc_id": "DCDC81",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/63-0040/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_VDD_3.3_C",
            "dcdc_id": "DCDC82",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/63-0040/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_CPLD_VDD_1.8_V",
            "dcdc_id": "DCDC83",
            "Min": 1620,
            "value": {
                "loc": "/sys/bus/i2c/devices/63-0040/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1980,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_CPLD_VDD_1.8_C",
            "dcdc_id": "DCDC84",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/63-0040/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 330,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_CPLD_VDD_3.3_V",
            "dcdc_id": "DCDC85",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/63-0040/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "SMB_CPLD_VDD_3.3_C",
            "dcdc_id": "DCDC86",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/63-0040/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MCB_FPGA_VDD1.0_V",
            "dcdc_id": "DCDC87",
            "Min": 900,
            "value": {
                "loc": "/sys/bus/i2c/devices/12-0040/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1100,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MCB_FPGA_VDD1.0_C",
            "dcdc_id": "DCDC88",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/12-0040/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 1188,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MCB_FPGA_VDD1.8_V",
            "dcdc_id": "DCDC89",
            "Min": 1620,
            "value": {
                "loc": "/sys/bus/i2c/devices/12-0040/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1980,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MCB_FPGA_VDD1.8_C",
            "dcdc_id": "DCDC90",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/12-0040/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MCB_FPGA_VDD1.2_V",
            "dcdc_id": "DCDC91",
            "Min": 1080,
            "value": {
                "loc": "/sys/bus/i2c/devices/12-0040/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1320,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MCB_FPGA_VDD1.2_C",
            "dcdc_id": "DCDC92",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/12-0040/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MCB_CPLD_VDD3.3_V",
            "dcdc_id": "DCDC93",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/12-0041/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MCB_CPLD_VDD3.3_C",
            "dcdc_id": "DCDC94",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/12-0041/hwmon/hwmon*/curr1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MCB_VDD3.3_V",
            "dcdc_id": "DCDC95",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/12-0041/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MCB_VDD3.3_C",
            "dcdc_id": "DCDC96",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/12-0041/hwmon/hwmon*/curr2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MCB_FPGA_VDD3.3_V",
            "dcdc_id": "DCDC97",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/12-0041/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "MCB_FPGA_VDD3.3_C",
            "dcdc_id": "DCDC98",
            "Min": -1000,
            "value": {
                "loc": "/sys/bus/i2c/devices/12-0041/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 550,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_P1V05_V",
            "dcdc_id": "DCDC99",
            "Min": 954,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in1_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1160,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_VCCIN_V",
            "dcdc_id": "DCDC100",
            "Min": 1350,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in2_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 2200,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_P1V2_VDDQ_V",
            "dcdc_id": "DCDC101",
            "Min": 1120,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1280,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_P1V8_V",
            "dcdc_id": "DCDC102",
            "Min": 1690,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1910,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_P0V6_VTT_V",
            "dcdc_id": "DCDC103",
            "Min": 558,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in5_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 682,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_VNN_PCH_V",
            "dcdc_id": "DCDC104",
            "Min": 540,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in6_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1320,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_VNN_NAC_V",
            "dcdc_id": "DCDC105",
            "Min": 540,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in7_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1320,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_P2V5_VPP_V",
            "dcdc_id": "DCDC106",
            "Min": 2250,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in8_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 2750,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_VCC_ANA_V",
            "dcdc_id": "DCDC107",
            "Min": 900,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in9_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1100,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_P3V3_STBY_V",
            "dcdc_id": "DCDC108",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in10_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_P5V_AUX_V",
            "dcdc_id": "DCDC109",
            "Min": 4000,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in11_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 5750,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_P1V8_AUX_V",
            "dcdc_id": "DCDC110",
            "Min": 1690,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in12_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1910,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_P3V3_AUX_V",
            "dcdc_id": "DCDC111",
            "Min": 2970,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in13_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3630,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_V1P80_EMMC_V",
            "dcdc_id": "DCDC112",
            "Min": 1690,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in14_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1910,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_V3P3_EMMC_V",
            "dcdc_id": "DCDC113",
            "Min": 3100,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005f/hwmon/hwmon*/in15_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 3500,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_VCCIN_V",
            "dcdc_id": "DCDC114",
            "Min": 1350,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-0070/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 2200,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_VCCIN_C",
            "dcdc_id": "DCDC115",
            "Min": -3100,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-0070/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 147000,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_P1V8_V",
            "dcdc_id": "DCDC116",
            "Min": 1690,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-0070/hwmon/hwmon*/in4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1910,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_P1V8_C",
            "dcdc_id": "DCDC117",
            "Min": -3100,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-0070/hwmon/hwmon*/curr4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 23000,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_P1V05_V",
            "dcdc_id": "DCDC118",
            "Min": 954,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-006e/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1160,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_P1V05_C",
            "dcdc_id": "DCDC119",
            "Min": -3100,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-006e/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 14300,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_VNN_PCH_V",
            "dcdc_id": "DCDC120",
            "Min": 540,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-006e/hwmon/hwmon*/in4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1320,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_VNN_PCH_C",
            "dcdc_id": "DCDC121",
            "Min": -3100,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-006e/hwmon/hwmon*/curr4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 74000,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_VNN_NAC_V",
            "dcdc_id": "DCDC122",
            "Min": 540,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-0068/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1320,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_VNN_NAC_C",
            "dcdc_id": "DCDC123",
            "Min": -3100,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-0068/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 22000,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_VCC_ANA_V",
            "dcdc_id": "DCDC124",
            "Min": 900,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-0068/hwmon/hwmon*/in4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 11000,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_VCC_ANA_C",
            "dcdc_id": "DCDC125",
            "Min": -3100,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-0068/hwmon/hwmon*/curr4_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 2210,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_P1V2_VDDQ_V",
            "dcdc_id": "DCDC126",
            "Min": 1120,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005e/hwmon/hwmon*/in3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "V",
            "Max": 1280,
            "format": "float(float(%s)/1000)",
        },

        {
            "name": "OCM_XDPE_P1V2_VDDQ_C",
            "dcdc_id": "DCDC127",
            "Min": -3100,
            "value": {
                "loc": "/sys/bus/i2c/devices/5-005e/hwmon/hwmon*/curr3_input",
                "way": "sysfs",
            },
            "read_times": 3,
            "Unit": "A",
            "Max": 19000,
            "format": "float(float(%s)/1000)",
        },
    ],
    "cpu": [
        {
            "name": "cpu",
            "reboot_cause_path": "/etc/sonic/.reboot/.previous-reboot-cause.txt"
        }
    ],
    "sfps": {
    }
}
