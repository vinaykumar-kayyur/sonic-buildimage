#!/usr/bin/env python

#############################################################################
# Dell S6100
#
# Platform and model specific eeprom subclass, inherits from the base class,
# and provides the followings:
# - the eeprom format definition
# - specific encoder/decoder if there is special need
#############################################################################

try:
    from sonic_eeprom import eeprom_tlvinfo
except ImportError, e:
    raise ImportError (str(e) + "- required module not found")


class board(eeprom_tlvinfo.TlvInfoDecoder):

    def __init__(self, name, path, cpld_root, ro):
        self.eeprom_path = "/sys/class/i2c-adapter/i2c-2/2-0050/eeprom"
        super(board, self).__init__(self.eeprom_path, 0, '', True)

    def serial_number_str(self, e):
        """Return Service Tag instead of serial number"""

        if self._TLV_HDR_ENABLED:
            tlv_no_header = e[self._TLV_INFO_HDR_LEN:] if self._TLV_HDR_ENABLED else e

        (is_valid, t) = self.get_tlv_index(tlv_no_header, self._TLV_CODE_SERVICE_TAG)

        if not is_valid:
            return "Bad service tag"

        t = tlv_no_header[t:]

        return t[2:2 + ord(t[1])]
