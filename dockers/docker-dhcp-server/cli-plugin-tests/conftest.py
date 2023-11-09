import pytest
import mock_tables # lgtm [py/unused-import]
from unittest import mock

@pytest.fixture()
def mock_db():
    db = mock.Mock()
    mock_data = {
        "STATE_DB": {
            "DHCP_SERVER_IPV4_LEASE|Vlan1000|10:70:fd:b6:13:00": {
                "lease_start": "1677640581",
                "lease_end": "1677641481",
                "ip": "192.168.0.1"
            },
            "DHCP_SERVER_IPV4_LEASE|Vlan1000|10:70:fd:b6:13:01": {
                "lease_start": "1677640581",
                "lease_end": "1677641481",
                "ip": "192.168.0.2"
            },
            "DHCP_SERVER_IPV4_SERVER_IP|eth0": {
                "ip": "240.127.1.2"
            },
            "FDB_TABLE|Vlan1000:10:70:fd:b6:13:00": {
                "port": "Ethernet10"
            },
            "FDB_TABLE|Vlan1000:10:70:fd:b6:13:01": {
                "port": "Ethernet11"
            }
        },
        "CONFIG_DB": {
            "DHCP_SERVER_IPV4|Vlan100": {
                "gateway": "100.1.1.1",
                "lease_time": "3600",
                "mode": "PORT",
                "netmask": "255.255.255.0",
                "customized_options": [
                    "option60"
                ],
                "state": "enabled"
            },
            "DHCP_SERVER_IPV4_CUSTOMIZED_OPTIONS|option60": {
                "id": "60",
                "type": "string",
                "value": "dummy_value"
            },
            "DHCP_SERVER_IPV4_RANGE|range1": {
                "ranges": [
                    "100.1.1.3",
                    "100.1.1.5"
                ]
            },
            "DHCP_SERVER_IPV4_RANGE|range2": {
                "ips": [
                    "100.1.1.7",
                    "100.1.1.8"
                ]
            },
            "DHCP_SERVER_IPV4_IP|eth0": {
                "ip": "240.127.1.2"
            }
        }
    }

    def keys(table):
        return mock_data[table].keys()

    def get_all(table, key):
        return mock_data[table][key]

    db.keys = mock.Mock(side_effect=keys)
    db.get_all = mock.Mock(side_effect=get_all)

    yield db
