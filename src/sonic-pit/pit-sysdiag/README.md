# `sysdiag` Design specification

`sysdiag`is a set of tools for testing switch hardware and software. Objective is perform health testing on a switch, generate test reports. It support environment test, development test and manufacturing test.

`sysdiag` Design basics

 * Standard test cases, hardware independent and deploy scenario independent;
 * Loggic of each test case is approved by all the users;
 * All inputs needed by a specific test case is read from corresponding configuration file;
 * All platform is manged via platform plugins(Stage 1, already supported) or platform APIs(Stage 2).

Due to the differences in the hardware design of each platform, it can be isolated through the configuration file of the platform layer.

### 1 Architecture

`sysdiag` overall architecture is shown in figure bellow. sysdiag include `test_cases`, i.e collection of all test cases, and `tools`, i.e collection of platform control tools.

```json
      ┌───────────────────────────────────────────────────────────┐
      │                        sysdiag                            │
      │  ┌────────────────┬───────────────┐      ┌─────────────┐  │
      │  │ test_caseA     │   fantool     │      │             │  │
      │  │ test_caseB     │   psutool     │      │  traffic    │  │
      │  │ test_caseZ     │   ...         │      │             │  │
      │  └────────────────┴───────────────┘      └─────────────┘  │
      │           ▲               ▲                ▲              │
      │           │               │                │              │
      └───────────┼───────────────┼────────────────┼──────────────┘
                  │               │                │
         ┌────────┴────────┬──────┴──────────┬─────┴───────────┐
middle   │                 │                 │                 │
abstract │   plugins       │ common_tools    │     bcmcmd      │
layer    │                 │                 │     ctc_shell   │
         └─────────────────┴─────────────────┴─────────────────┘


         ┌─────────────────────────────────┐ ┌─────────────────┐
         │                                 │ │                 │
kernel   │           hardware drivers      │ │     asic        │
space    │                                 │ │                 │
         └─────────────────────────────────┘ └─────────────────┘
```

### 2 `plugins` middle layer of abstraction
`plugins` is platform abstraction layer in SONiC, `sysdiag` utilize these modules to control platform hardware.
Example listed below are `plugins` that are generic(platform indepedent). In the cases where `sysdiag` want to access information except bellow items, platform specific tools or sysfs case be used.

* `CPU`：`/proc/cpuinfo` or `dmidecode`
* `memory`：`/proc/meminfo` or `dmidecode`
* `SSD`：`mmc-util` or `smartctl`
* `RTC`：`/sys/class/rtc/rtc0/*`



#### 2.1 `sfputil.py`
`sfputil.py` is used to access SFP/QSFP/OSFP modules. Test cases focus on I/O status of optic modules and EEPROM read/write of the optic modules. Required methods are listed below:

``` python
class SfpUtil(SfpUtilBase):
    # Get sfp port list
    @property
    def sfp_port_list(self):
        '''
        SFP Ports list
        @return LIST [1, 2, 3, ...]
        '''
        return LIST

    # Get QSFP port list
    @property 
    def qsfp_ports(self):
        '''
        QSFP Ports list
        @return LIST [1, 2, 3, ...]
        '''
        return LIST

    # Get sysfs path map of the switch, return a dict for all ports, key is port number
    @property
    def port_to_eeprom_mapping(self):
        '''
        dictionary where key=physical port index(integer), value=path to SFP EEPROM file(string)
        @return DICT {
            1: None,
            2: '/sys/bus/i2c/devices/10-0050/eeprom'
        }
        '''
        return DICT

    # Get optic module presence status
    def get_presence(self, port_index):
        return True/False

    # Get QSFP module interrupt status
    def get_interrupt(self, port_index):
        return True/False

    # Get QSFP module low power mode
    def get_low_power_mode(self, port_index):
        return True/False
    def set_low_power_mode(self, port_index, enable):
        return True/False

    # Get QSFP module reset pin status
    def get_reset(self, port_index):
        return True/False

    def reset(self, port_index):
        return True/False

    # Get SFP/QSFP tx fault
    def get_tx_fault(self, port_index):
        return True/False

    # Get SFP/QSFP rx los
    def get_rx_los(self, port_index):
        return True/False

    # Get SFP/QSFP tx disable
    def get_tx_disable(self, port_index):
        return True/False

    def set_tx_disable(self, port_index, enable):
        return True/False

    # Eload support low speed signals monitor/control
    # For sfp
    def get_eload_tx_disable(self, port_index):
        return True/False

    def set_eload_tx_fault(self, port_index, enable):
        return True/False

    def set_eload_rx_los(self, port_index, enable):
        return True/False

    # SFP port set mod_abs pin while QSFP port set modprs pin
    def set_eload_presence(self, port_index, enable):
        return True/False

    # For qsfp
    def get_eload_low_power_mode(self, port_index):
        return True/False

    def get_eload_reset_changed(self, port_index):
        '''
            when set eload modprstL high, port cpld will reset qsfp;
            we need call below function to check wether reset changed or not
        '''
        return True/False

    def set_eload_interrupt(self, port_index, enable):
        return True/False

    # eload power setting
    def set_eload_power(self, port_index, value):
        return True/False

    # eload insertion counter
    def get_eload_insertion_counter(self, port_index):
        return integer

    # Get port SFP/QSFP plugin/out records
    def get_plug_record(self):
        '''
        present bit in CPLD logic is set to clear_on_read, so we shoudl read all ports' presence data.
        return dict, key=physical port index(integer), value=True if plug happend else False.
        @return DICT {
            1: False,
            2: True,
        }
        ''' 
        return {
            1:True,
            2:False,
        }

    # SFP/QSFP change events
    def get_transceiver_change_event(self, timeout=0):
        return DICT
```

`sysdiag`may obtain port layout by `sfputil.py` then run tranceiver tests.


#### 2.2 `fanutil.py`
`fanutil.py`主要实现风扇访问控制，支持转速查看、占空比设置等。需要实现接口如下：
`fanutil.py` implements fan control, support fan speed, pwm settings, etc. It should implements the following methods:

```python
class FanUtil(object):
    def __init__(self):
        pass

    def get_num_fans(self):
        """
        Retrieves the number of FANs supported on the device
        """
        return FAN_NUM
    
    def get_fan_presence(self, index):
        """
        Retrieves the presence status of FAN defined by 1-based index <index>
        @index: An integer, 1-based index of the FAN
        @return: Boolean, True if FAN is plugged, False if not
        """
        return True/False
    
    def get_all(self):
        """
        Retrieves the FANs information
        @return DICT
        """
        return {
            "Number": 1,
            "FAN1": {
                    "Present": True,
                    "Running": True,
                    "Speed": 12000.0,
                    "pwm": 124,
                    "LowThd": 5400.0,
                    "HighThd": 20000.0,
                    "SN": "serial_number_example",  # 'N/A'
                    "PN": "part_number_exampple",   # 'N/A'
                    "Status": True,
                    "AirFlow": "F2B",               # 'N/A'
                    }
            }

    # Set fan speed
    def set_speed(self, fan, pwm):
        # @fan: fan index;
        # @pwm: pwm value [0 ~ 100];
        return True/False

    # Set fan speed to full speed, highest priority
    def set_full_speed(self, enable):
        return True/False

    # Set fan control mode(auto/manual)
    def set_mode(self, mode):
        return True/False

```

#### 2.3 `psuutil.py`
`psuuti.py`implement PSU information access.

```python
class PsuUtil(PsuBase):
    
    def get_num_psus(self):
        """
        Retrieves the number of PSUs supported on the device
        """
        return PSU_NUM

    def get_psu_status(self, index):
        """
        Retrieves the operational status of PSU
        @index: An integer, 1-based index of PSU of which to query status
        @return: Boolean, True if PSU is operating properly, False if PSU is faulty
        """
        return True/False
    
    def get_all(self):
        return {
            "Number": PSU_NUM,
            "PSU1": {
                    "Present": True,
                    "InputType": "AC" or "DC",
                    "InputStatus": True/False,
                    "OutputStatus": True/False,
                    "AirFlow": "F2B",
                    "SN": "serial_number_example",
                    "PN": "part_number_exampple",
                    "Vendor": "Vendor_name",
                    "HwVersion": "1.0",
                    "FwVersion": "1.0",
                    "Fan": {
                        "Value": 1100,
                        "LowThd": 100,
                        "HighThd": 2000,
                        "Unit": "rpm"
                    },
                    "Temperature": {
                        "Value": 1100,
                        "LowThd": 100,
                        "HighThd": 2000,
                        "Unit": "C"
                    },
                    "InputsPower": {
                        "Value": 111.1,
                        "LowThd": 111.1,
                        "HighThd": 111.1,
                        "Unit": 'W',
                    },
                    "OutputsPower": {
                        "Value": 111.1,
                        "LowThd": 111.1,
                        "HighThd": 111.1,
                        "Unit": 'W',
                    },
                    "InputsVoltage": {
                        "Value": 111.1,
                        "LowThd": 111.1,
                        "HighThd": 111.1,
                        "Unit": 'V',
                    },
                    "OutputsVoltage": {
                        "Value": 111.1,
                        "LowThd": 111.1,
                        "HighThd": 111.1,
                        "Unit": 'V',
                    },
                    "InputsCurrent": {
                        "Value": 111.1,
                        "LowThd": 111.1,
                        "HighThd": 111.1,
                        "Unit": 'A',
                    },
                    "OutputsCurrent": {
                        "Value": 111.1,
                        "LowThd": 111.1,
                        "HighThd": 111.1,
                        "Unit": 'A',
                    }
            }
        }

    def set_psu_fan_speed(self, psu_index, pwm):
        """
        set psu fan speed.
        @psu_index: An integer, 1-based index of PSU
        @pwm: An integer, rang is [0 ~ 100]
        """
        return True/False
    
```

#### 2.4 `sensorutil.py`
`sensorutil.py` implements `sensor` information access. It should implements methods as below:
```python
class SensorUtil(object):
    def __init__(self):
        pass

    def get_num_sensors(self):
        """
        Retrieves the number of Sensors supported on the device
        """
        return SENSOR_NUM

    def get_all(self):
        return {
            "EMC1403-I2C-3-5C":{
                "Present":True,
                "CPU_TEMP": {
                    "Value": 12.0,
                    "LowThd": 54.0,
                    "HighThd": 65.0,
                    "Unit": "C",
                    "Description":"CPU TEMP"
                }，
                "Inlet_Temp": {
                    "Value": 12.0,
                    "LowThd": 54.0,
                    "HighThd": 65.0,
                    "Unit": "C",
                    "Description":"SMB Inlet TEMP"
                },
            },
            "ADC128D818-I2C-9-1F":{
                "Present":True,
                "P3V3_SW": {
                    "Value": 3.2,
                    "LowThd": 3.0,
                    "HighThd": 3.4,
                    "Unit": 'V',
                    "Description":""
                },
            },
            "PSU-I2C-4-59":{
                "Present":True,
                "PSU1_CIN": {
                    "Value": 23.0,
                    "LowThd": 0,
                    "HighThd": 25,
                    "Unit": 'A',
                    "Description":""
                },
                "PSU1_VIN": {
                    "Value": 220,
                    "LowThd": 182,
                    "HighThd": 290,
                    "Unit": 'V',
                    "Description":""
                },
                "PSU1_PIN": {
                    "Value": 550,
                    "LowThd": 0,
                    "HighThd": 600,
                    "Unit": 'W',
                    "Description":""
                },
            },
        }
```

#### 2.5 `fwmgrutil.py`
`fwmgrutil.py` implements firmware version get, firmware upgrade, firmware refresh for logical devices, such as CPLD, FPGA, PCIe, and system components such as BIOS, UBoot and BMC os. It should implements below methods:

```python
class FwMgrUtil(object):
    def __init__(self):
        pass

    def get_fw_version(self):
        """
        Retrieves all firmwares' version on the device
        @return DICT, key=firmware name, value=DICT,include "version" and "description"
        """
        return 
        {
            "BIOS":{
                "Desc":"Basic Input/Output System",
                "Version":"2.0.1"
            },
            "BSP":{
                "Desc":"BSP Driver",
                "Version":"2.0.1"
            },
            "CPU_CPLD":{
                "Desc":"COMe Board CPLD",
                "Version":"2.0.2"
            },
            "CPU_IR3584_1":{
                "Desc":"CPU PVDDQ VR",
                "Version":"2.0.0"
            },
        }

    # BIOS
    def get_bios_current_boot_flash(self):
        return "master"/"slave"

    def get_bios_next_boot_flash(self):
        return "master"/"slave"

    def set_bios_next_boot_flash(self, flash):
        return True/False

    # Uboot
    def get_uboot_current_boot_flash(self):
        return "master"/"slave"

    def get_uboot_next_boot_flash(self):
        return "master"/"slave"

    def set_uboot_next_boot_flash(self, flash):
        return True/False

    # BMC
    def get_bmc_current_boot_flash(self):
        return "master"/"slave"

    def get_bmc_next_boot_flash(self):
        return "master"/"slave"

    def set_bmc_next_boot_flash(self, flash):
        return True/False

    def firmware_upgrade(self, fw_type, fw_path, fw_extr=None):
        """
        @fw_type: firmware type, should be one of the strings:'bios', 'uboot', 'bmc', 'cpld', .etc.
        @fw_path: target firmware file
        @fw_extra OPTIONAL, extra information string, for fw_type 'BIOS'/'Uboot'/'BMC', value should be one of 'master'/'slave'/'both'
        @return: Boolean
        """
        return True/False

    def firmware_refresh(self, fw_type, fw_path, fw_extra=None):
        return True/False

    # Get FRU name list of system components, such as system, switch board, power board, fan board, etc.
    def get_frus(self):
        """
        Retrieves all FRU names on the device
        @return: LIST
        """
        return FRU_NAME_LIST  # ['sys', 'smb', 'pdb']

    # Get FRU information of a given system component
    def read_fru(self, fru_name):
        """
        Read the FRU content.
        @fru_name: string, the name of FRU
        @return: TUPLE,(status, output), status=True if FRU acceed success,
                 output=string of the FRU content.
        """
        return statue, content

    # Burn FRU info into EEPROM of a system components
    def program_fru(self, fru_name, fru_bin_file):
        """
        program the FRU
        @fru_name: the name of FRU
        @fru_bin_file: the file of FRU raw binary.
        @return: True if programed success.
        """
        return True/False
```

#### 2.6 `led_control.py`
`led_control.py` implements front panel ports' `LEDs` and device's system `LEDs` controls. It should implements methods bellow:

```python
class LedControl(LedControlBase):
    # 设置panel sys led
    def set_sys_led(self, color):
        """
        @color: string，should be one of "red"/'green'/'yellow' , hardware supported color
        """
        return True/False

    # Set panel power led
    def set_power_led(self, color):
        return True/False

    # Set system fan led
    def set_fan_led(self, color):
        return True/False

    # Set system bmc led if applicable
    def set_bmc_led(self, color):
        return True/False

    # Set front panel port leds
    def set_port_led(self, color):
        return True/False

    # Set fan module led
    def set_fan_module_led(self, color):
        return True/False

    # Set psu module led
    def set_psu_module_led(self, color):
        return True/False

    # Set system location led
    def set_location_led(self, color):
        return True/False

    # Get supported components name list of LED control
    def get_leds(self):
        return LED_NAME_LIST #['sys', 'power', 'fan', 'port']

```

#### 2.7 `mgmtport.py`
`mgmtport.py` implements control of management ethernet port, usually eth0. It implements methods bellow:

```python
class MgmtPortUtil(object):
    def __init__(self):
        pass

    def get_all(self):
        """
        Retrieves the management port running status
        @return: DICT
        """
        return {
            "Link": True/False,
            "Firmware": "3.25",
            "Speed": "1000" or "100" or "10",
            "Duplex": "full" or "half",
            "AN": True/False,
        }

```

For Host side, `sysdiag` may access management interface by read/write registers.
For BMC side, `sysdiag` may access mangement interface through RESTful APIs.

#### 2.8 `bmcutil.py`
`bmcutil.py` implements BMC control and BMC diagnostic. It should implements methods listed below:

```python
class BmcUtil(object):
    def __init__(self):
        pass

    def run_bmc_diag(self, case=None):
        """
        Run bmc test cases

        @case: case name; if not specified case name, then run all cases.
        @return: TUPLE (status, output), status=Boolean, output=string of case returned.
        """
        if not case:
            test_all()
        else:
            test_one(case)
        return (status, output)

    def reboot_bmc(self):
        return True/False

    # Exec commands on BMC side
    def exec_raw_cmd(self, command):
        """
        Run command under BMC OS 
        @command: command string,
        @return: TUPLE (status, output), status=Boolean, output=string of case returned.
        """
        return (status, output)

```

#### 2.9 `fruidutil.py` FRU read/write tool
`fruidutil.py` implements FRU info read/write.

``` Shell

"""
        FRU Commands:  list read write edit
        fru list                                             - list all fru
        fru list <type num>                                  - list specific fru data
        fru read <type num> <fru file>                       - store fru data to file
        fru write <type num> <fru file>                      - write fru data from file
        fru edit <type num> field <section> <index> <string> - edit FRU string

        You should move fru file to /usr/local/bin first
"""

"""
fruidutil get [NODE+NUM]
          set [NODE+NUM] -f <file>

OPTIONS:    
    option                     <get|set> fru information
    node                       <fan1|fan2|psu1|...>fru node name 
    -f                         Path of xxx.bin file
    -h                         Print use guide
"""
```

#### 2.10 `syseeprom-write.py` 
`syseeprom-write.py` read/write sys-eeprom information.

``` Shell

'''
    write tlv eeprom to eeprom

    Usage:
        syseeprom-write.py <JSON_Path>

    e.g.:
        syseeprom-write.py ../config/common/syseeprom_test.json
'''
```


### 3 `sysdiag` implementation
`sysdiag` source tree:

```shell
.
├── readme.md
├── cases
│   ├── cpu_tc
│   │   └── config.json
│   ├── memory_tc
│   │   └── config.json
│   ├── rtc_tc
│   │   └── config.json
│   ├── ssd_tc
│   ├── replaceable_eeprom_read_tc
│   │   └── config.json
│   ├── replaceable_eeprom_write_tc
│   │   └── config.json
│   ├── slot_eeprom_read_tc
│   │   └── config.json
│   ├── slot_eeprom_write_tc
│   │   └── config.json
│   └── ...
│       └── config.json
├── config
│   └── platform
│       ├── arm64-alibaba_as61_48e4t_lc-r0
│       │   ├── case_config.json
│       │   └── platform_config.json
│       ├── arm64-alibaba_as61_48x4t_lc-r0
│       ├── x86_64-h3c_s9825-64d-w1-r0
│       │   ├── case_config.json
│       │   └── platform_config.json
│       └── ...
│           ├── case_config.json
│           └── platform_config.json
└── src
    ├── cpu_tc.py
    ├── tlv_eeprom_read_tc.py
    ├── errcode.py
    ├── sysdiag.py
    ├── ...
```

All test cases implementation file end with subfix`_tc.py` are placed under directory src.
`test_case.py` defines test case base class.
`sysdiag.py` defines main function, parse options, create test case and run test cases per user's input, generate test result per test case and conclude a final result.

Directory `cases/` contains all the configuration file for each test case.
Direcotry `config/` contains all the configuration file per platform.
Confiugration file detail:


* Test case configuration:

  * `config.json`: This file describe test case, reference Alibaba design doc.

    ```json
    {
        "name": "tlv-eeprom-test",               // Test case name
        "description": "Test system TLV EEPROM", // Test case functional description
        "type": "auto",                          // Test case type, e.g automation test
        "tags": ["manufacture", "delivery"],     // Test case scenario, manufacture, acceptant test
        "expectation": {                         // Result expectation
            "override": "enable",
            "Serial Number": {
                "type": "string",
                "prefix": "R1241FCL",
                "subfix": "none",
                "keywords": [],
                "length": 19
            },
            "Part Number": {
                "type": "regex",
                "pattern": "R1241-F[A-Z]{4}-[0-9]{2}"
            }
        }
    }
    ```

    

* Platform configuration:

  * `platform_config.json`: this file defines test cases full set supported by this platform

    ```json
    {
        "test_cases": [                    // supported test cases
            "i2c_tc",
            "emmc_tc",
            "tlv_eeprom_tc",
            "tlv_eeprom_read_tc",
            "tlv_eeprom_write_tc",
            "replaceable_eeprom_read_tc",
            "replaceable_eeprom_write_tc",
            "slot_eeprom_read_tc",
            "slot_eeprom_write_tc"
        ]
    }
    ```
    
    * `case_config.json`: this file defines test case specific variables, such as i2c topo
  
      ```json
      {
          "fan_info":{
              "count":6,
              "ratio_target": [10,80,20],
              "speed_tolerance": 1000,
              "speed_max": 20000,
              "speed_min": 0,
              "motor_count": 2
          }
      }
      ```


#### 3.1 `syslogger` Log utility
It defines class `SysLogger`, log file defaults to `/var/log/sysdiag.log`, log file size `20MB` each, rotate and keeps 5 backup file at most.

Log levels are `log_dbg`、`log_info`、`log_warn`、`log_err`、`log_crit`. By default, log only to log file and print to console is an option.
 

#### 3.2 Main class `sysdiag`

`CLI` command line description

```shell
$ sysdiag -h
=================================================================
  ____ ___ _____           ____            ____  _             
 |  _ \_ _|_   _|         / ___| _   _ ___|  _ \(_) __ _  __ _ 
 | |_) | |  | |    _____  \___ \| | | / __| | | | |/ _` |/ _` |
 |  __/| |  | |   |_____|  ___) | |_| \__ \ |_| | | (_| | (_| |
 |_|  |___| |_|           |____/ \__, |___/____/|_|\__,_|\__, |
                                 |___/                   |___/ 
=================================================================

         2021-01-15 17:56:33

sysdiag

    System diagnostic test utility

Usage:
    sysdiag [FUNCTION] [OPTIONS...]

FUNCTION:
    -v, --version                      Show sysdiag version
    -d, --diag [-g <tag>] [-t <type>]  Run diagnostic test, default tag is delivery
    -s, --single <casefile>            Run single test, test case file should be given
    -l, --list [-g <tag>]              Show all possible cases, default tag is delivery

OPTIONS:
    -h, --help                         Print sysdiag user guide
    -c, --chinese                      Test outputs in Chinese
    -q, --quiet                        don't print status messages to stdout")
    -t, --type                         <auto|manual|utility>    Specify type of test cases, default type is auto
    -g, --tag                          <delivery|manufacture|emc|power|pa>  Specify tag of test cases, default tag is delivery
    -i, --interval                     <min>    Set test interval when loop test, unit minute
    -b, --break                        Break when error occured under performance test
    -p, --pre handle                   pre handle

```


Class `SysDiag` defines the user interfaces and main processing logic of the `pit-sysdiag`. It get users' input, parse options and arguments, then decide which kind of test to run, run all the cases, generate final results.

First, `parse_opts_and_args()` is used to parse options and arguments, supports options like -d/-l/-s, etc.

Next step, it generate a list of test cases interpreted from options and arguments. Then loads test cases with `imp.load_source` and `getattr` method to instantiate each test case, then link them in a list, i.e `self.test_case_list`.

Then comes the main loop, it iterates over all the test case instances, invokes `run()` method, with each case instance may generate its own result in a JSON file.

Finally, after all cases in the list finish running, all test case result will be collected to generate a final result, also store in a JSON file with a call to method `generate_final_result()`.


#### 3.3 `test_case` Design
`test_case.py` defines the base class `TCBase`. This class implements read test case configuration file, i.e `config.json`, parse it, then execute the test logic, generate a test result.


##### Methods of class `TCBase`:
* `def __init__(self, index, case_cfg_file)`:
  The constructor.
  `@index` the index of the test case
  `@case_cfg_file` the configuration file of the test case
  It will load config file and initialize everything, provides date for methods `get_tc_xxx` APIs.

* `def run_test(self, *argv):`:
  User should override this method, as each test case's testing logic is placed here

* `def generate_result(self, code):`:
  Generic method, for generating test result for each test.

  e.g.
  ```python
  def generate_result(self, code):
      result = "Pass" if code==E.OK else "Fail"
      msg = "Test case {}: [{}] =======> {}".format(self.case_index, self.get_tc_name(), result)
      err = "ErrorCode: {}\nFail reasons: {}".format(code.name, self.fail_reason)
      return msg, err
  ```

* `def generate_result_dict(self,code)`:
  Generic method, generates the result with a dict, with some pre-defined keys.

Note that, `run_test()` should also return an error code, which is used by `sysdiag` loop, to obtain the result directly.

* `self.fail_reason = [*, *, *]`
  This is a list of stirngs, holds the fail reason messages if there is any, or empty list if all test cases passed.

* `return`: return an error code, E.OK for success.


`test_case.py` defines class `TestCaseCommon`, inherit from `TCBase`, it load and parse `$platform/case_cofnig.json` file.


##### Class `TestCaseCommon` methods:

* `def __init__(self, index, module_name, logger, platform_cfg_file, case_cfg_file=None)`:
  The constructor.
  `@index`: index of a test case, used for sorting or managing test sequence.
  `@module_name`: test case name
  `@logger`: logging facility
  `@platform_cfg_file`: platform specific config file, i.e `config/platform/$platfor_name/case_config.json`
  `@case_cfg_file`: test case config file, defaults to `cases/$module_name/config.json`


File naming and class naming rules:

1. Test case file name should be `xxxx_tc.py`, where `xxxx` is test case name. e.g. `fan_tc.py` for fan test.

2. Test case class name should be `class XXXXTC(TestCaseCommon), where `TC` for 'TestCase', 'XXXX' should be the same as 'xxxx'(the file name) except in Capital format. e.g. `fan_tc.py` contains a class `FANTC(TestCaseCommon)`.

3. `moduole_name` should be the same as test case file name without `.py` subfix. e.g. `MODULE_NAME="fan_tc"` is defined in `fan_tc.py`, then `fan_tc` is test case name in `config/cases/$test_case_name/case_config.json`.

   ```
   class FANTC(TestCaseCommon):
       def __init__(self, index, logger, platform_cfg_file, case_cfg_file=None):
           MODULE_NAME = "fan_tc"
           TestCaseCommon.__init__(self, index, MODULE_NAME, logger, platform_cfg_file, case_cfg_file)
   ```

 
An example: how to implement a test case `i2c` test.

Step 1) What
Check if all the I2C devices in the system are functional.

Step 2) How to
Access all the devices under i2c buses, check the status of each device, test read/write function. For devices not writable, do read-only test. Devices of interest may be `CPLD`, `SFP EEPROM`, `FRU`, `RTC`, etc.

Step 3) Implementation in derived test case, i.e `class I2CTC(TestCaseCommon)' in `i2c_tc.py`, put the logic in Step 2 into method `run_test()`.

Addtionally, `i2c` test case require I2C topo of the platform, so we add configuration in to file `config/platform/*/case_config.json` as follow:

```json
{
    "i2c":{
        "CTRL_CPLD" : {
            "bus" : 2,
            "address" : "0x0d",
            "register" : "0x0F",
            "flag" : "rw"
        },
        "PORT1_CPLD" : {
            "bus" : 3,
            "address" : "0x30",
            "register" : "0x0F",
            "flag" : "rw"
        },
    ...
}
```

class `i2c` defined as:

```python
class I2CTC(TestCaseCommon):
    def __init__(self, index, logger, platform_cfg_file, case_cfg_file=None):
        MODULE_NAME = "i2c_tc" # this param specified the case config dirictory
        TestCaseCommon.__init__(self, index, MODULE_NAME, logger, platform_cfg_file, case_cfg_file)
        try:
            if self.platform_cfg_json and 'i2c' in self.platform_cfg_json.keys():
                self.i2c_devices = self.platform_cfg_json['i2c_topo']
        except Exception as e:
            self.logger.log_err(str(e))
            self.i2c_devices = None
```

Implement method `i2c_device_rw_test` as: iterate over all devices, access them, log failed cases with failed_reason string and append this failed_reason string in self.failed_reason list.

```python
def i2c_device_rw_test(self, also_print_console=False):
    '''
        i2c device read/write test
    '''
```

`run_test` simply invoke `i2c_device_rw_test`.



#### 3.4 Error code definition
File `errorcode.py` defines all the error code used in `pit-sysdiag`, examples:

```python
class E(Enum):
    OK = 0           # pass
    EFAIL = 1        # fail
    EUSB1000 = 1000  # usb not found
    EUSB1001 = 1001  # usb write error
    ...
```
Each test case may import errorcode directly.

#### 3.5 Test caase `xxxx_tc.py` reference implementation

```python
from test_case import TestCaseCommon
from errcode import E

class XXXXTC(TestCaseCommon):
    def __init__(self, index, logger, platform_cfg_file, case_cfg_file=None):
        MODULE_NAME = "xxxx_tc"  # this param specified the case config dirictory
        TestCaseCommon.__init__(self, index, MODULE_NAME, logger, platform_cfg_file, case_cfg_file)
    
    def test_a(self):
        if fail:
            self.fail_reason.append("usb not found")
            return E.EUSB1000
        else:
            return E.OK
    
    def test_b(self):
        if fail:
            self.fail_reason.append("usb write error")
            return E.EUSB1001
        else:
            return E.OK
    
    # Mandatory
    def run_test(self, *argv):
        ret = self.test_a()
        if ret != E.OK:
            return ret.value
        ret = self.test_b()
        return ret.value

```
