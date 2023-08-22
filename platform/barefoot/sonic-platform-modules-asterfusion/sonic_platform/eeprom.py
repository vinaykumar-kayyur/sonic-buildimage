##############################################################################
# Asterfusion CX-T Devices EEPROM                                            #
#                                                                            #
# Platform and model specific eeprom subclass, inherits from the base class, #
# and provides the followings:                                               #
# - the eeprom format definition                                             #
# - specific encoder/decoder if there is special need                        #
#                                                                            #
##############################################################################

try:
    import binascii
    import copy
    import os
    import struct
    import sys

    from .constants import *
    from .helper import APIHelper

    from sonic_platform_base.sonic_eeprom.eeprom_tlvinfo import TlvInfoDecoder
except ImportError as err:
    raise ImportError(str(err) + "- required module not found")

CACHE_ROOT = "/var/cache/sonic/decode-syseeprom"
CACHE_FILE = "syseeprom_cache"
EEPROM_CACHE = os.path.join(CACHE_ROOT, CACHE_FILE)
EEPROM_CACHE_DIR = os.path.dirname(EEPROM_CACHE)


class Tlv(TlvInfoDecoder):
    """Platform-specific EEPROM class"""

    def __init__(self, helper, hwver, hwsku, platform):
        super(Tlv, self).__init__(EEPROM_CACHE, 0, "", True)
        self._api_helper = helper  # type: APIHelper
        # Init device
        self.hwver = hwver
        self.hwsku = hwsku
        self.platform = platform
        # Init eeprom
        self._eeprom = {}
        self._init_eeprom()

    def _init_eeprom(self):
        # fmt: off
        eeprom_keycode_mapping = (
            # TlvInfo Header:
            #    Id String:    TlvInfo
            #    Version:      1
            #    Total Length: 169
            #                               # TLV Name            Code Len Value
            # Key                  Code     # ------------------- ---- --- -----
            ("prod_name",         "0x21"),  # Product Name        0x21  11 X312P-48Y-T
            ("prod_part_num",     "0x22"),  # Part Number         0x22   7 CME3000
            ("prod_ser_num",      "0x23"),  # Serial Number       0x23   8 18120001
            ("ext_mac_addr",      "0x24"),  # Base MAC Address    0x24   6 00:11:22:33:44:55
            ("sys_mfg_date",      "0x25"),  # Manufacture Date    0x25  19 12/31/2018 23:59:59
            ("prod_ver",          "0x26"),  # Device Version      0x26   1 0
            ("prod_sub_ver",      "0x27"),  # Label Revision      0x27   1 0
            ( "prod_arch",        "0x28"),  # Platform Name       0x28  30 x86_64-asterfusion_cx312p_48y_
            ("onie_version",      "0x29"),  # ONIE Version        0x29  10 2018.07.31
            ("ext_mac_addr_size", "0x2a"),  # MAC Addresses       0x2A   2 1
            ("sys_mfger",         "0x2b"),  # Manufacturer        0x2B  11 Asterfusion
            ("country_code",      "0x2c"),  # Manufacture Country 0x2C   2 CN
            ("vendor_name",       "0x2d"),  # Vendor Name         0x2D  11 Asterfusion
            ("diag_version",      "0x2e"),  # Diag Version        0x2E   3 1.0
            ("serv_tag",          "0x2f"),  # Service Tag         0x2F   1 X
            ("crc32",             "0xfe"),  # CRC-32              0xFE   4 0x8AFC983D
        )
        # fmt: on
        eeprom_keycode_dict = dict(eeprom_keycode_mapping)

        with self._api_helper.thrift_connect() as client:
            eeprom_keyvalue_dict = vars(client.pltfm_mgr_sys_eeprom_get())

        for key in eeprom_keyvalue_dict:
            if eeprom_keyvalue_dict[key] is None:
                eeprom_keyvalue_dict[key] = 0
            if key == "ext_mac_addr":
                eeprom_keyvalue_dict[key] = eeprom_keyvalue_dict[key][:17]
                self._api_helper.validate_mac_addr(eeprom_keyvalue_dict[key])
            elif key == "prod_ver" or key == "prod_sub_ver":
                eeprom_keyvalue_dict[key] = int(eeprom_keyvalue_dict[key])
            elif key == "ext_mac_addr_size":
                eeprom_keyvalue_dict[key] = int(eeprom_keyvalue_dict[key])
            elif key != "crc32":
                eeprom_keyvalue_dict[key] = str(eeprom_keyvalue_dict[key])

        self._cache_eeprom(copy.deepcopy(eeprom_keyvalue_dict))
        eeprom_keyvalue_dict = filter(
            lambda kv: kv[0] in eeprom_keycode_dict.keys(), eeprom_keyvalue_dict.items()
        )
        self._eeprom = dict(
            map(lambda kv: (eeprom_keycode_dict[kv[0]], kv[1]), eeprom_keyvalue_dict)
        )

    def _cache_eeprom(self, eeprom_values):
        # fmt: off
        eeprom_codes = (
            # TlvInfo Header:
            #    Id String:    TlvInfo
            #    Version:      1
            #    Total Length: 169
            #                                # TLV Name            Code Len Value
            # Key                   Code     # ------------------- ---- --- -----
            ("prod_name",         b"\x21"),  # Product Name        0x21  11 X312P-48Y-T
            ("prod_part_num",     b"\x22"),  # Part Number         0x22   7 CME3000
            ("prod_ser_num",      b"\x23"),  # Serial Number       0x23   8 18120001
            ("ext_mac_addr",      b"\x24"),  # Base MAC Address    0x24   6 00:11:22:33:44:55
            ("sys_mfg_date",      b"\x25"),  # Manufacture Date    0x25  19 12/31/2018 23:59:59
            ("prod_ver",          b"\x26"),  # Device Version      0x26   1 0
            ("prod_sub_ver",      b"\x27"),  # Label Revision      0x27   1 0
            ("prod_arch",         b"\x28"),  # Platform Name       0x28  30 x86_64-asterfusion_cx312p_48y_
            ("onie_version",      b"\x29"),  # ONIE Version        0x29  10 2018.07.31
            ("ext_mac_addr_size", b"\x2a"),  # MAC Addresses       0x2A   2 1
            ("sys_mfger",         b"\x2b"),  # Manufacturer        0x2B  11 Asterfusion
            ("country_code",      b"\x2c"),  # Manufacture Country 0x2C   2 CN
            ("vendor_name",       b"\x2d"),  # Vendor Name         0x2D  11 Asterfusion
            ("diag_version",      b"\x2e"),  # Diag Version        0x2E   3 1.0
            ("serv_tag",          b"\x2f"),  # Service Tag         0x2F   1 X
            ("crc32",             b"\xfe"),  # CRC-32              0xFE   4 0x8AFC983D
        )
        # fmt: on
        eeprom_header = b"TlvInfo\x00\x01\x00"
        eeprom_length = 0
        eeprom_content = b""

        for key, code in eeprom_codes:
            if key in eeprom_values:
                eeprom_value = eeprom_values[key]
                if eeprom_value is None:
                    eeprom_value = 0

                if key == "ext_mac_addr":
                    value = binascii.unhexlify("".join((eeprom_value[:17]).split(":")))
                elif key == "prod_ver" or key == "prod_sub_ver":
                    value = binascii.unhexlify(format(int(eeprom_value), "02x"))
                elif key == "ext_mac_addr_size":
                    value = b"\x00"
                    value += binascii.unhexlify(format(int(eeprom_value), "02x"))
                elif key == "crc32":
                    value = b"\x00\x00\x00\x00"
                else:
                    if type(eeprom_value) is int:
                        eeprom_value = str(eeprom_value)
                    value = b""
                    for char in eeprom_value:
                        value += binascii.unhexlify(format(ord(char), "02x"))

                length = struct.pack("B", len(value))

                eeprom_content += code + length + value
                eeprom_length += len(value) + 2

        eeprom_length = struct.pack("B", eeprom_length)
        eeprom_raw = eeprom_header + eeprom_length + eeprom_content
        eeprom_no_crc = eeprom_raw[:-4]
        crc = binascii.crc32(eeprom_no_crc) & 0xFFFFFFFF
        if sys.version_info.major == 3:
            crc_data = (
                binascii.unhexlify(format(int((crc & 0xFF000000) >> 24), "02x"))
                + binascii.unhexlify(format(int((crc & 0x00FF0000) >> 16), "02x"))
                + binascii.unhexlify(format(int((crc & 0x0000FF00) >> 8), "02x"))
                + binascii.unhexlify(format(int((crc & 0x000000FF)), "02x"))
            )
        else:
            crc_data = (
                chr((crc & 0xFF000000) >> 24)
                + chr((crc & 0x00FF0000) >> 16)
                + chr((crc & 0x0000FF00) >> 8)
                + chr(crc & 0x000000FF)
            )
        eeprom_raw = eeprom_no_crc + crc_data

        if not os.path.exists(EEPROM_CACHE_DIR):
            os.makedirs(EEPROM_CACHE_DIR, exist_ok=True)
        eeprom_cache = open(os.path.join(CACHE_ROOT, CACHE_FILE), "wb")
        eeprom_cache.write(eeprom_raw)
        eeprom_cache.close()

    def get_eeprom(self):
        return self._eeprom

    def get_serial(self):
        return self._eeprom.get("0x23", "Undefined.")

    def get_mac(self):
        return self._eeprom.get("0x24", "Undefined.")
