import pytest
from unittest import mock

import os
import json
import sys


modules_path = os.path.join(os.path.dirname(__file__), "../../../src/sonic-utilities")
test_path = os.path.join(modules_path, "tests")
mock_table_path = os.path.join(test_path, "mock_tables")
sys.path.insert(0, modules_path)
sys.path.insert(0, test_path)
sys.path.insert(0, mock_table_path)


TEST_DATA_PATH = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def mock_db():
    db = mock.Mock()

    with open(TEST_DATA_PATH + "mock_config_db.json") as f:
        s = f.read()
        mock_config_db = json.loads(s)
    with open(TEST_DATA_PATH + "mock_state_db.json") as f:
        s = f.read()
        mock_state_db = json.loads(s)

    def keys(table):
        assert table == "CONFIG_DB" or table == "STATE_DB"
        if table == "CONFIG_DB":
            return mock_config_db.keys()
        if table == "STATE_DB":
            return mock_state_db.keys()


    def get_all(table, key):
        assert table == "CONFIG_DB" or table == "STATE_DB"
        if table == "CONFIG_DB":
            return mock_config_db[table][key]
        if table == "STATE_DB":
            return mock_state_db[table][key]

    db.keys = mock.Mock(side_effect=keys)
    db.get_all = mock.Mock(side_effect=get_all)

    yield db
