import filecmp
import os
import subprocess

from unittest import TestCase
import tests.common_utils as utils

class TestBgpTemplate(TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.realpath(__file__))
        self.minigraph_dir = os.path.join(self.test_dir, 'minigraph')
        self.script_file = os.path.join(self.test_dir, '..', 'sonic-cfggen')
        self.output_file = os.path.join(self.test_dir, 'output')

        self.m0_minigraph = os.path.join(self.minigraph_dir, 'MWH01-0100-0202-01M0.xml')
        self.mc0_minigraph = os.path.join(self.minigraph_dir, 'MWH01-0100-0202-01MC0.xml')

        self.hlx_port_config = os.path.join(self.test_dir, 'hlx-port-config.ini')

        self.deployment_id_asn_map = os.path.join(self.test_dir, 'deployment_id_asn_map.yml')
        self.device_metadata = os.path.join(self.test_dir, 'device_metadata.json')

    def run_script(self, argument):
        print('CMD: sonic-cfggen ' + argument)
        output = subprocess.check_output(self.script_file + ' ' + argument, shell=True)

        if utils.PY3x:
            output = output.decode()

        return output

    def run_diff(self, file1, file2):
        output = subprocess.check_output('diff -u {} {} || true'.format(file1, file2), shell=True)

        if utils.PY3x:
            output = output.decode()

        return output

    def run_bgpd_template_test(self, minigraph, port_config, valid_result_file):
        template_dir = os.path.join(self.test_dir, '..', '..', '..', 'dockers', 'docker-fpm-frr', "frr")
        conf_template = os.path.join(template_dir, 'bgpd', 'bgpd.conf.j2')
        constants = os.path.join(self.test_dir, '..', '..', '..', 'files', 'image_config', 'constants', 'constants.yml')
        argument = '-m {} -p {} -y {} -t {} -T {} > {}'.format(minigraph, port_config, constants, conf_template, template_dir, self.output_file)
        self.run_script(argument)

        expected = os.path.join(self.test_dir, 'sample_output', valid_result_file)
        self.assertTrue(filecmp.cmp(expected, self.output_file), self.run_diff(expected, self.output_file))

    def test_bgpd_m0(self):
        self.run_bgpd_template_test(self.m0_minigraph, self.hlx_port_config, 'MWH01-0100-0202-01M0.bgpd.conf')

    def test_bgpd_mc0(self):
        self.run_bgpd_template_test(self.mc0_minigraph, self.hlx_port_config, 'MWH01-0100-0202-01MC0.bgpd.conf')

    def tearDown(self):
        try:
            pass
            os.remove(self.output_file)
        except OSError:
            pass
