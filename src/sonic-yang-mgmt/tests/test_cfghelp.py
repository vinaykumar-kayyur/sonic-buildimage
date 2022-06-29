import json
import subprocess
import os

from unittest import TestCase

output1="""\
Error: Table or all option is required
usage: sonic-cfg-help [-h] [-t TABLE] [-f FIELD] [-p PRINT_FORMAT] [-a]

Description of table name

optional arguments:
  -h, --help            show this help message and exit
  -t TABLE, --table TABLE
                        Table name
  -f FIELD, --field FIELD
                        Field
  -p PRINT_FORMAT, --print_format PRINT_FORMAT
                        Print format
  -a, --all             Print all tables
"""

techsupport_table_output="""\

AUTO_TECHSUPPORT
Description: AUTO_TECHSUPPORT part of config_db.json

+-----------------------+----------------------------------------------------+-------------+-----------+-------------+
| Field                 | Description                                        | Mandatory   | Default   | Reference   |
+=======================+====================================================+=============+===========+=============+
| state                 | Knob to make techsupport invocation event-driven   |             |           |             |
|                       | based on core-dump generation                      |             |           |             |
+-----------------------+----------------------------------------------------+-------------+-----------+-------------+
| rate_limit_interval   | Minimum time in seconds between two successive     |             |           |             |
|                       | techsupport invocations. Configure 0 to explicitly |             |           |             |
|                       | disable                                            |             |           |             |
+-----------------------+----------------------------------------------------+-------------+-----------+-------------+
| max_techsupport_limit | Max Limit in percentage for the cummulative size   |             |           |             |
|                       | of ts dumps. No cleanup is performed if the value  |             |           |             |
|                       | isn't configured or is 0.0                         |             |           |             |
+-----------------------+----------------------------------------------------+-------------+-----------+-------------+
| max_core_limit        | Max Limit in percentage for the cummulative size   |             |           |             |
|                       | of core dumps. No cleanup is performed if the      |             |           |             |
|                       | value isn't congiured or is 0.0                    |             |           |             |
+-----------------------+----------------------------------------------------+-------------+-----------+-------------+
| since                 | Only collect the logs & core-dumps generated since |             |           |             |
|                       | the time provided. A default value of '2 days ago' |             |           |             |
|                       | is used if this value is not set explicitly or a   |             |           |             |
|                       | non-valid string is provided                       |             |           |             |
+-----------------------+----------------------------------------------------+-------------+-----------+-------------+

"""

techsupport_table_field_output="""\

AUTO_TECHSUPPORT
Description: AUTO_TECHSUPPORT part of config_db.json

+---------+--------------------------------------------------+-------------+-----------+-------------+
| Field   | Description                                      | Mandatory   | Default   | Reference   |
+=========+==================================================+=============+===========+=============+
| state   | Knob to make techsupport invocation event-driven |             |           |             |
|         | based on core-dump generation                    |             |           |             |
+---------+--------------------------------------------------+-------------+-----------+-------------+

"""

portchannel_table_field_output="""\

PORTCHANNEL
Description: PORTCHANNEL part of config_db.json

key - name
+---------+-------------------------------------------+-------------+-----------+-------------+
| Field   | Description                               | Mandatory   | Default   | Reference   |
+=========+===========================================+=============+===========+=============+
| members | The field contains list of unique members |             |           | PORT:name   |
+---------+-------------------------------------------+-------------+-----------+-------------+

"""

dscp_to_tc_table_field_output="""\

DSCP_TO_TC_MAP
Description: DSCP_TO_TC_MAP part of config_db.json

key - name
+---------+------------------------------------------------------+-------------+-----------+-------------+
| Field   | Description                                          | Mandatory   | Default   | Reference   |
+=========+======================================================+=============+===========+=============+
| name    |                                                      |             |           |             |
+---------+------------------------------------------------------+-------------+-----------+-------------+
| dscp    | This field is for storing mapping between two fields |             |           |             |
+---------+------------------------------------------------------+-------------+-----------+-------------+
| tc      | This field is for storing mapping between two fields |             |           |             |
+---------+------------------------------------------------------+-------------+-----------+-------------+

"""

acl_rule_table_field_output="""\

ACL_RULE
Description: ACL_RULE part of config_db.json

key - ACL_TABLE_NAME:RULE_NAME
+-----------+-----------------------------------------+-------------+-----------+-------------+
| Field     | Description                             | Mandatory   | Default   | Reference   |
+===========+=========================================+=============+===========+=============+
| ICMP_TYPE | Mutually exclusive in group icmp        |             |           |             |
|           | when IP_TYPE in ANY,IP,IPV4,IPv4ANY,ARP |             |           |             |
+-----------+-----------------------------------------+-------------+-----------+-------------+

"""

class TestCfgHelp(TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.realpath(__file__))
        self.script_file = 'python ' + os.path.join(self.test_dir, '..', 'sonic-cfg-help')

    def run_script(self, argument):
        print('\n    Running sonic-cfg-help ' + argument)
        output = subprocess.check_output(self.script_file + ' ' + argument, shell=True)

        output = output.decode()

        linecount = output.strip().count('\n')
        if linecount <= 0:
            print('    Output: ' + output.strip())
        else:
            print('    Output: ({0} lines, {1} bytes)'.format(linecount + 1, len(output)))
        return output

    def test_dummy_run(self):
        argument = ''
        output = self.run_script(argument)
        self.assertEqual(output, output1)

    def test_single_table(self):
        argument = '-t AUTO_TECHSUPPORT'
        output = self.run_script(argument)
        self.assertEqual(output, techsupport_table_output)

    def test_single_field(self):
        argument = '-t AUTO_TECHSUPPORT -f state'
        output = self.run_script(argument)
        self.assertEqual(output, techsupport_table_field_output)

    def test_leaf_list(self):
        argument = '-t PORTCHANNEL -f members'
        output = self.run_script(argument)
        print(output)
        self.assertEqual(output, portchannel_table_field_output)

    def test_leaf_list_map(self):
        argument = '-t DSCP_TO_TC_MAP'
        output = self.run_script(argument)
        print(output)
        self.assertEqual(output, dscp_to_tc_table_field_output)

    def test_when_condition(self):
        argument = '-t ACL_RULE -f ICMP_TYPE'
        output = self.run_script(argument)
        print(output)
        self.assertEqual(output, acl_rule_table_field_output)
