"""
Copyright(c)2012 Iwan Budi Kusnanto
"""
import time

import nyamuk_const as NC
import mqtt_types   as t


# PROPERTIES ID
PROP_PAYLOAD_FORMAT_INDICATOR  = 0x01
PROP_MSG_EXPIRY_INTERVAL       = 0x02
PROP_CONTENT_TYPE              = 0x03
PROP_RESP_TOPIC                = 0x08
PROP_CORRELATION_DATA          = 0x09
PROP_SUBSCR_ID                 = 0x0B
PROP_SESS_EXPIRY_INTERVAL      = 0x11
PROP_ASSIGNED_CLIENT_ID        = 0x12
PROP_SRV_KEEPALIVE             = 0x13
PROP_AUTH_METHOD               = 0x15
PROP_AUTH_DATA                 = 0x16
PROP_REQUEST_PROBLEM_NFO       = 0x17
PROP_WILL_DELAY_INTERVAL       = 0x18
PROP_REQ_RESP_NFO              = 0x19
PROP_RESP_NFO                  = 0x1A
PROP_SRV_REF                   = 0x1C
PROP_REASON_STRING             = 0x1F
PROP_RECV_MAX                  = 0x21
PROP_TOPIC_ALIAS_MAX           = 0x22
PROP_TOPIC_ALIAS               = 0x23
PROP_MAX_QOS                   = 0x24
PROP_RETAIN_AVAILABLE          = 0x25
PROP_USR_PROPERTY              = 0x26
PROP_MAX_PKT_SIZE              = 0x27
PROP_WILDCARD_SUBSCR_AVAILABLE = 0x28
PROP_SUBSCR_ID_AVAILABLE       = 0x29
PROP_SHARED_SUBSCR_AVAILABLE   = 0x2A

class NyamukProp(object):
    """Nyamuk property."""
    def __init__(self, prop_id, value):
        """
            name: one of properties (ie PROP_USR_PROPERTY)
        """
        self.id    = prop_id
        self.type  = PROPS_DATA[prop_id][0]
        self.value = value

    def len(self):
        """
            Compute property length

            NOTE: about "1+"
            property is made of property type (var byte int) followed by property value

            currently all property types are 1 byte long, so to speedup a bit we don't compute
            its length (may be required in the future)
        """
        # length variable is either an integer (static value) or a function (variable length)
        length = t.DATATYPE_OPS[self.type][t.DATATYPE_LEN]
        if type(length) == int:
            return 1 + length

        return 1 + length(self.value)

    def write(self, packet):
        packet.write_byte(self.id)
        getattr(packet, t.DATATYPE_OPS[self.type][t.DATATYPE_WR])(self.value)

    def __repr__(self):
        return "{0} ({1})".format(PROPS_DATA[self.id][1], self.value)

class ServerKeepAlive(NyamukProp):
    def __init__(self, keepalive):
        super(ServerKeepAlive, self).__init__(PROP_SRV_KEEPALIVE, keepalive)

class UserProperty(NyamukProp):
    def __init__(self, (key, value)):
        super(UserProperty, self).__init__(PROP_USR_PROPERTY, (key, value))

#TODO: a class for all properties

"""
class SessionExpiryInterval(NyamukProp):
    def __init__(self, interval=0):
        super(SessionExpiryInterval, self).__init__(t.DATATYPE_BYTE, interval)

"""

PROP_DATA_TYPE  = 0
PROP_DATA_DESC  = 1
PROP_DATA_CLASS = 2

# per property: datatype, description, class
PROPS_DATA = {
    0x01: [t.DATATYPE_BYTE     , "PAYLOAD FORMAT INDICATOR"      , NyamukProp],
    0x02: [t.DATATYPE_UINT32   , "MESSAGE EXPIRY INTERVAL"       , NyamukProp],
    0x03: [t.DATATYPE_UTF8     , "CONTENT TYPE"                  , NyamukProp],
    0x08: [t.DATATYPE_UTF8     , "RESPONSE TOPIC"                , NyamukProp],
    0x09: [t.DATATYPE_BYTES    , "CORRELATION DATA"              , NyamukProp],
    0x0B: [t.DATATYPE_VARINT   , "SUBSCRIPTION ID"               , NyamukProp],
    0x11: [t.DATATYPE_UINT32   , "SESSION_EXPIRY_INTERVAL"       , NyamukProp],
    0x12: [t.DATATYPE_UTF8     , "ASSIGNED CLIENT ID"            , NyamukProp],
    0x13: [t.DATATYPE_UINT16   , "SERVER KEEPALIVE"              , ServerKeepAlive],
    0x15: [t.DATATYPE_UTF8     , "AUTH METHOD"                   , NyamukProp],
    0x16: [t.DATATYPE_BYTES    , "AUTH DATA"                     , NyamukProp],
    0x17: [t.DATATYPE_BYTE     , "REQUEST PROBLEM INFO"          , NyamukProp],
    0x18: [t.DATATYPE_UINT32   , "WILL DELAY INTERVAL"           , NyamukProp],
    0x19: [t.DATATYPE_BYTE     , "REQUEST RESPONSE INFO"         , NyamukProp],
    0x1A: [t.DATATYPE_UTF8     , "RESPONSE INFO"                 , NyamukProp],
    0x1C: [t.DATATYPE_UTF8     , "SERVER REFERE"                 , NyamukProp],
    0x1F: [t.DATATYPE_UTF8     , "REASON STRING"                 , NyamukProp],
    0x21: [t.DATATYPE_UINT16   , "RECEIVE MAXIMUM"               , NyamukProp],
    0x22: [t.DATATYPE_UINT16   , "TOPIC ALIAS MAXIMUM"           , NyamukProp],
    0x23: [t.DATATYPE_UINT16   , "TOPIC ALIAS"                   , NyamukProp],
    0x24: [t.DATATYPE_BYTE     , "MAXIMUM QOS"                   , NyamukProp],
    0x25: [t.DATATYPE_BYTE     , "RETAIN AVAILABLE"              , NyamukProp],
    0x26: [t.DATATYPE_UTF8_PAIR, "USER PROPERTY"                 , UserProperty],
    0x27: [t.DATATYPE_UINT32   , "MAX PACKET SIZE"               , NyamukProp],
    0x28: [t.DATATYPE_BYTE     , "WILDCARD SUBCRIPTION AVAILABLE", NyamukProp],
    0x29: [t.DATATYPE_BYTE     , "SUBSCRIPTION ID AVAILABLE"     , NyamukProp],
    0x2A: [t.DATATYPE_BYTE     , "SHARE SUBSCRIPTION AVAILABLE"  , NyamukProp],
}

