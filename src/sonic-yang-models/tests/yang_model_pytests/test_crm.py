import pytest


thresholds = [
    'free', 'FREE',
    'used', 'USED',
    'percentage', 'PERCENTAGE'
]


@pytest.fixture(params=thresholds)
def threshold(request):
    return request.param


resources = [
    'ipv4_route',
    'ipv6_route',
    'ipv4_nexthop',
    'ipv6_nexthop',
    'ipv4_neighbor',
    'ipv6_neighbor',
    'nexthop_group_member',
    'nexthop_group',
    'fdb_entry',
    'mpls_nexthop',
    'srv6_nexthop'
]


@pytest.fixture(params=resources)
def resource(request):
    return request.param


class TestCrm:

    def test_crm_valid_data(self, yang_model, resource, threshold):
        data = {
            "sonic-crm:sonic-crm": {
                "sonic-crm:CRM": {
                    "Config": {
                        f"{resource}_high_threshold": 95,
                        f"{resource}_low_threshold": 70,
                        f"{resource}_threshold_type": threshold
                    }
                }
            }
        }

        yang_model.load_data(data)

    @pytest.mark.parametrize(
        "high, low, error_message", [
            (-1, 70, 'Invalid value "-1"'),
            (100, -70, 'Invalid value "-70"'),
            (10, 70, 'high_threshold should be more than low_threshold')]
        )
    def test_crm_thresholds(self, yang_model, resource, threshold, high, low, error_message):
        data = {
            "sonic-crm:sonic-crm": {
                "sonic-crm:CRM": {
                    "Config": {
                        f"{resource}_high_threshold": high,
                        f"{resource}_low_threshold": low,
                        f"{resource}_threshold_type": threshold
                    }
                }
            }
        }

        yang_model.load_data(data, error_message)

    @pytest.mark.parametrize(
        "high, low, th_type, error_message", [
            (100, 70, 'wrong', 'Value "wrong" does not satisfy the constraint'),
            (110, 20, 'percentage', 'Must condition')]
        )
    def test_crm_threshold_type(self, yang_model, resource, high, low, th_type, error_message):
        data = {
            "sonic-crm:sonic-crm": {
                "sonic-crm:CRM": {
                    "Config": {
                        f"{resource}_high_threshold": high,
                        f"{resource}_low_threshold": low,
                        f"{resource}_threshold_type": th_type
                    }
                }
            }
        }

        yang_model.load_data(data, error_message)
