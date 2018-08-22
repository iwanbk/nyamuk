"""
Copyright(c)2012 Iwan Budi Kusnanto
"""
import time

import nyamuk_const as NC

class NyamukProp:
    """Nyamuk property."""
    def __init__(self, name, value):
        """
            name: one of properties (ie PROP_USR_PROPERTY)
        """
        self.name  = name
        self.type  = NC.PROPS_DATA_TYPE[name]
        self.value = value

    def len(self):
        """
            Compute property length

            NOTE: about "1+"
            property is made of property type (var byte int) followed by property value

            currently all property types are 1 byte long, so to speedup a bit we don't compute
            its length (may be required in the future)
        """
        length = NC.DATATYPE_LEN[self.type]
        if type(length) == int:
            return 1 + length

        return 1 + length(self.value)

    def write(self, packet):
        NC.write_byte(packet, self.name)
        NC.DATATYPE_RW_OPS[self.type][0](packet, self.value)

    def __repr__(self):
        return "{0} ({1})".format(NC.PROPS_NAME[self.name], self.value)


"""
class SessionExpiryInterval(NyamukProp):
    def __init__(self, interval=0):
        super(SessionExpiryInterval, self).__init__(NC.DATATYPE_BYTE, interval)

"""

