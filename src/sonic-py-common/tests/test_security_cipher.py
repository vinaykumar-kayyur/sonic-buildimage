import sys

if sys.version_info.major == 3:
    from unittest import mock
else:
    import mock

import pytest
from sonic_py_common.security_cipher import security_cipher
from .mock_swsscommon import ConfigDBConnector

# TODO: Remove this if/else block once we no longer support Python 2
if sys.version_info.major == 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"

DEFAULT_FILE = [
        "#Auto generated file for storing the encryption passwords",
        "TACPLUS : ",
        "RADIUS : ", 
        "LDAP :"
        ]

UPDATED_FILE = [
        "#Auto generated file for storing the encryption passwords",
        "TACPLUS : ",
        "RADIUS : TEST2",
        "LDAP :"
        ]


class TestSecurityCipher(object):
    def test_passkey_encryption(self):
        with mock.patch("sonic_py_common.security_cipher.ConfigDBConnector", new=ConfigDBConnector), \
             mock.patch("{}.open".format(BUILTINS),mock.mock_open()) as mock_file:
            temp = security_cipher()

            # Use patch to replace the built-in 'open' function with a mock
            with mock.patch("{}.open".format(BUILTINS), mock.mock_open()) as mock_file:
                mock_fd = mock.MagicMock()
                mock_fd.readlines = mock.MagicMock(return_value=DEFAULT_FILE)
                mock_file.return_value.__enter__.return_value = mock_fd 
                encrypt, err = temp.encrypt_passkey("TACPLUS", "passkey1", "TEST1")
                assert encrypt !=  "passkey1"
                assert err == None 

    def test_passkey_decryption(self):
        with mock.patch("sonic_py_common.security_cipher.ConfigDBConnector", new=ConfigDBConnector), \
             mock.patch("{}.open".format(BUILTINS), mock.mock_open()) as mock_file:
            temp = security_cipher()

            # Use patch to replace the built-in 'open' function with a mock
            with mock.patch("{}.open".format(BUILTINS), mock.mock_open()) as mock_file:
                mock_fd = mock.MagicMock()
                mock_fd.readlines = mock.MagicMock(return_value=DEFAULT_FILE)
                mock_file.return_value.__enter__.return_value = mock_fd
                encrypt, err = temp.encrypt_passkey("RADIUS", "passkey2", "TEST2")
                assert err == None

            # Use patch to replace the built-in 'open' function with a mock
            #with mock.patch("{}.open".format(BUILTINS), mock.mock_open(read_data=EXPECTED_PASSWD)) as mock_file:
            with mock.patch("{}.open".format(BUILTINS), mock.mock_open()) as mock_file:
                mock_fd = mock.MagicMock()
                mock_fd.readlines = mock.MagicMock(return_value=UPDATED_FILE)
                mock_file.return_value.__enter__.return_value = mock_fd 
                decrypt, err = temp.decrypt_passkey("RADIUS", encrypt)
                assert err == None 
                assert decrypt == "passkey2"


