import os
import json
import pytest


from app.template import TemplateFabric
from app.config import ConfigMgr


TEMPLATE_PATH = os.path.abspath('../../dockers/docker-fpm-frr/frr')

# ToDo: Check for gloabl for ipv6. route-map _must be_ in the v6 instance or peer-group.

def load_tests(path):
    param_files = [name for name in os.listdir(path)
                   if os.path.isfile(os.path.join(path, name)) and name.startswith("param_")]
    tests = []
    for param_fname in param_files:
        casename = param_fname.replace("param_", "").replace(".json", "")
        result_fname = "result_%s.conf" % casename
        full_param_fname = os.path.join(path, param_fname)
        full_result_fname = os.path.join(path, result_fname)
        tests.append((casename, full_param_fname, full_result_fname))
    return tests

def load_json(fname):
    with open(fname) as param_fp:
        raw_params = json.load(param_fp)
    params = {}
    for table_key, table_entries in raw_params.items():
        if table_key.startswith("CONFIG_DB__"):
            # convert CONFIG_DB__* entries keys into tuple if needed
            new_table_entries = {}
            for entry_key, entry_value in table_entries.items():
                if '|' in entry_key:
                    new_key = tuple(entry_key.split('|'))
                else:
                    new_key = entry_key
                new_table_entries[new_key] = entry_value
            params[table_key] = new_table_entries
        else:
            params[table_key] = table_entries
    return params

def compress_comments(raw_config):
    comment_counter = 0
    output = []
    for line in raw_config.split('\n'):
        stripped_line = line.strip()
        # Skip empty lines
        if stripped_line == '':
            pass
        # Write lines without comments
        elif not stripped_line.startswith('!'):
            if comment_counter > 0:
                output.append("!")
                comment_counter = 0
            output.append(line)
        # Write non-empty comments
        elif stripped_line.startswith('!') and len(stripped_line) > 1:
            if comment_counter > 0:
                output.append("!")
                comment_counter = 0
            output.append(line)
        # Count empty comments
        else: # stripped_line == '!'
            comment_counter += 1
    # Flush last comment if we have one
    if comment_counter > 0:
        output.append("!")
    return "\n".join(output) + "\n"

def write_result(fname, raw_result):
    with open(fname, 'w') as fp:
        raw_result_w_commpressed_comments = compress_comments(raw_result)
        fp.write(raw_result_w_commpressed_comments)

def run_tests(test_name, template_fname, tests):
    tf = TemplateFabric(TEMPLATE_PATH)
    template = tf.from_file(template_fname)
    for case_name, param_fname, result_fname in tests:
        params = load_json(param_fname)
        raw_generated_result = str(template.render(params))
        assert "None" not in raw_generated_result, "Test %s.%s" % (test_name, case_name)
        write_result(result_fname, raw_generated_result)
        canonical_generated_result = ConfigMgr.to_canonical(raw_generated_result)
        with open(result_fname) as result_fp:
            raw_saved_result = result_fp.read()
        canonical_saved_result = ConfigMgr.to_canonical(raw_saved_result)
        assert canonical_saved_result == canonical_generated_result, "Test %s.%s" % (test_name, case_name)

# Tests

def test_general_policies():
    tests = load_tests("tests/data/general/policies.conf")
    tmpl_fname = os.path.join("bgpd", "templates", "general", "policies.conf.j2")
    run_tests("general_policies", tmpl_fname, tests)

def test_general_pg():
    tests = load_tests("tests/data/general/peer-group.conf")
    tmpl_fname = os.path.join("bgpd", "templates", "general", "peer-group.conf.j2")
    run_tests("general_pg", tmpl_fname, tests)

def test_general_instance():
    tests = load_tests("tests/data/general/instance.conf")
    tmpl_fname = os.path.join("bgpd", "templates", "general", "instance.conf.j2")
    run_tests("general_instance", tmpl_fname, tests)

def test_dynamic_policies():
    tests = load_tests("tests/data/dynamic/policies.conf")
    tmpl_fname = os.path.join("bgpd", "templates", "dynamic", "policies.conf.j2")
    run_tests("dynamic_policies", tmpl_fname, tests)

def test_dynamic_pg():
    tests = load_tests("tests/data/dynamic/peer-group.conf")
    tmpl_fname = os.path.join("bgpd", "templates", "dynamic", "peer-group.conf.j2")
    run_tests("dynamic_pg", tmpl_fname, tests)

def test_dynamic_instance():
    tests = load_tests("tests/data/dynamic/instance.conf")
    tmpl_fname = os.path.join("bgpd", "templates", "dynamic", "instance.conf.j2")
    run_tests("dynamic_instance", tmpl_fname, tests)

def test_monitors_policies():
    tests = load_tests("tests/data/monitors/policies.conf")
    tmpl_fname = os.path.join("bgpd", "templates", "monitors", "policies.conf.j2")
    run_tests("monitors_policies", tmpl_fname, tests)

def test_monitors_pg():
    tests = load_tests("tests/data/monitors/peer-group.conf")
    tmpl_fname = os.path.join("bgpd", "templates", "monitors", "peer-group.conf.j2")
    run_tests("monitors_pg", tmpl_fname, tests)

def test_monitors_instance():
    tests = load_tests("tests/data/monitors/instance.conf")
    tmpl_fname = os.path.join("bgpd", "templates", "monitors", "instance.conf.j2")
    run_tests("monitors_instance", tmpl_fname, tests)
