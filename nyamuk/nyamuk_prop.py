"""
Copyright(c)2012 Iwan Budi Kusnanto
"""
import time

import nyamuk_const as NC
import mqtt_types   as t

__all__ = [
    # properties infos
    'get_property_type', 'get_property_description', 'get_property_class', 'get_property_instance',
    # property classes
    'PayloadFormatIndicator', 'MessageExpiryInterval', 'ContentType', 'ResponseTopic',
    'CorrelationData', 'SubscriptionIdentifier', 'SessionExpiryInterval', 'AssignedClientId',
    'ServerKeepAlive', 'AuthenticationMethod', 'AuthenticationData', 'RequestProblemInformation',
    'WillDelayInterval', 'RequestResponseInformation', 'ResponseInformation', 'ServerReference',
    'ReasonString', 'ReceiveMaximum', 'TopicAliasMaximum', 'TopicAlias', 'MaximumQos',
    'RetainAvailable', 'UserProperty', 'MaximumPacketSize', 'WildcardSubscriptionAvailable',
    'SubscriptionIdentifierAvailable', 'SharedSubscriptionAvailable'
]

# PROPERTIES ID
PROP_PAYLOAD_FORMAT_INDIC  = 0x01
PROP_MSG_EXPIRY_INTERVAL   = 0x02
PROP_CONTENT_TYPE          = 0x03
PROP_RESP_TOPIC            = 0x08
PROP_CORRELATION_DATA      = 0x09
PROP_SUBSCR_ID             = 0x0B
PROP_SESS_EXPIRY_INTERVAL  = 0x11
PROP_ASSIGNED_CLIENT_ID    = 0x12
PROP_SRV_KEEPALIVE         = 0x13
PROP_AUTH_METHOD           = 0x15
PROP_AUTH_DATA             = 0x16
PROP_REQUEST_PROBLEM_NFO   = 0x17
PROP_WILL_DELAY_INTERVAL   = 0x18
PROP_REQ_RESP_NFO          = 0x19
PROP_RESP_NFO              = 0x1A
PROP_SRV_REF               = 0x1C
PROP_REASON_STRING         = 0x1F
PROP_RECV_MAX              = 0x21
PROP_TOPIC_ALIAS_MAX       = 0x22
PROP_TOPIC_ALIAS           = 0x23
PROP_MAX_QOS               = 0x24
PROP_RETAIN_AVAIL          = 0x25
PROP_USR_PROPERTY          = 0x26
PROP_MAX_PKT_SIZE          = 0x27
PROP_WILDCARD_SUBSCR_AVAIL = 0x28
PROP_SUBSCR_ID_AVAIL       = 0x29
PROP_SHARED_SUBSCR_AVAIL   = 0x2A

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
        """
            Write property on packet flow
        """
        packet.write_byte(self.id)
        getattr(packet, t.DATATYPE_OPS[self.type][t.DATATYPE_WR])(self.value)

    def __repr__(self):
        return "{0}: {1}".format(PROPS_DATA[self.id][PROP_DATA_DESC], self.value)


class PayloadFormatIndicator(NyamukProp):
    def __init__(self, format_indicator=0x00):
        super(PayloadFormatIndicator, self).__init__(PROP_PAYLOAD_FORMAT_INDIC, format_indicator)

class MessageExpiryInterval(NyamukProp):
    def __init__(self, expiry):
        super(MessageExpiryInterval, self).__init__(PROP_MSG_EXPIRY_INTERVAL, expiry)

class ContentType(NyamukProp):
    def __init__(self, content_type):
        super(ContentType, self).__init__(PROP_CONTENT_TYPE, content_type)

class ResponseTopic(NyamukProp):
    def __init__(self, topic):
        super(ResponseTopic, self).__init__(PROP_RESP_TOPIC, topic)

class CorrelationData(NyamukProp):
    def __init__(self, data):
        super(CorrelationData, self).__init__(PROP_CORRELATION_DATA, data)

class SubscriptionIdentifier(NyamukProp):
    def __init__(self, subscr_id):
        super(SubscriptionIdentifier, self).__init__(PROP_SUBSCR_ID, subscr_id)

class SessionExpiryInterval(NyamukProp):
    def __init__(self, expiry):
        super(SessionExpiryInterval, self).__init__(PROP_SESS_EXPIRY_INTERVAL, expiry)

class AssignedClientId(NyamukProp):
    def __init__(self, client_id):
        super(AssignedClientId, self).__init__(PROP_ASSIGNED_CLIENT_ID, client_id)

class ServerKeepAlive(NyamukProp):
    def __init__(self, keepalive):
        super(ServerKeepAlive, self).__init__(PROP_SRV_KEEPALIVE, keepalive)

class AuthenticationMethod(NyamukProp):
    def __init__(self, auth_method):
        super(AuthenticationMethod, self).__init__(PROP_AUTH_METHOD, auth_method)

class AuthenticationData(NyamukProp):
    def __init__(self, auth_data):
        super(AuthenticationData, self).__init__(PROP_AUTH_DATA, auth_data)

class RequestProblemInformation(NyamukProp):
    def __init__(self, info):
        super(RequestProblemInformation, self).__init__(PROP_REQUEST_PROBLEM_NFO, info)

class WillDelayInterval(NyamukProp):
    def __init__(self, will_delay):
        super(WillDelayInterval, self).__init__(PROP_WILL_DELAY_INTERVAL, will_delay)

class RequestResponseInformation(NyamukProp):
    def __init__(self, info):
        super(RequestResponseInformation, self).__init__(PROP_REQ_RESP_NFO, info)

class ResponseInformation(NyamukProp):
    def __init__(self, info):
        super(ResponseInformation, self).__init__(PROP_RESP_NFO, info)

class ServerReference(NyamukProp):
    def __init__(self, ref):
        super(ServerReference, self).__init__(PROP_SRV_REF, ref)

class ReasonString(NyamukProp):
    def __init__(self, reason):
        super(ReasonString, self).__init__(PROP_REASON_STRING, reason)

class ReceiveMaximum(NyamukProp):
    def __init__(self, value):
        super(ReceiveMaximum, self).__init__(PROP_RECV_MAX, value)

class TopicAliasMaximum(NyamukProp):
    def __init__(self, value):
        super(TopicAliasMaximum, self).__init__(PROP_TOPIC_ALIAS_MAX, value)

class TopicAlias(NyamukProp):
    def __init__(self, topic_alias):
        super(TopicAlias, self).__init__(PROP_TOPIC_ALIAS, topic_alias)

class MaximumQos(NyamukProp):
    def __init__(self, max_qos):
        super(MaximumQos, self).__init__(PROP_MAX_QOS, max_qos)

class RetainAvailable(NyamukProp):
    def __init__(self, retain_available):
        super(RetainAvailable, self).__init__(PROP_RETAIN_AVAIL, retain_available)

class UserProperty(NyamukProp):
    def __init__(self, (key, value)):
        super(UserProperty, self).__init__(PROP_USR_PROPERTY, (key, value))

class MaximumPacketSize(NyamukProp):
    def __init__(self, max_pkt_size):
        super(MaximumPacketSize, self).__init__(PROP_MAX_PKT_SIZE, max_pkt_size)

class WildcardSubscriptionAvailable(NyamukProp):
    def __init__(self, wildcard_subscr_available):
        super(WildcardSubscriptionAvailable, self).__init__(PROP_WILDCARD_SUBSCR_AVAIL, wildcard_subscr_available)

class SubscriptionIdentifierAvailable(NyamukProp):
    def __init__(self, subscr_id_available):
        super(SubscriptionIdentifierAvailable, self).__init__(PROP_SUBSCR_ID_AVAIL, subscr_id_available)

class SharedSubscriptionAvailable(NyamukProp):
    def __init__(self, shared_subscr_available):
        super(SharedSubscriptionAvailable, self).__init__(PROP_SHARED_SUBSCR_AVAIL, shared_subscr_available)


PROP_DATA_TYPE  = 0
PROP_DATA_DESC  = 1
PROP_DATA_CLASS = 2

# per property: datatype, description, class
PROPS_DATA = {
    0x01: [t.DATATYPE_BYTE     , "PAYLOAD FORMAT INDICATOR"      , PayloadFormatIndicator],
    0x02: [t.DATATYPE_UINT32   , "MESSAGE EXPIRY INTERVAL"       , MessageExpiryInterval],
    0x03: [t.DATATYPE_UTF8     , "CONTENT TYPE"                  , ContentType],
    0x08: [t.DATATYPE_UTF8     , "RESPONSE TOPIC"                , ResponseTopic],
    0x09: [t.DATATYPE_BYTES    , "CORRELATION DATA"              , CorrelationData],
    0x0B: [t.DATATYPE_VARINT   , "SUBSCRIPTION ID"               , SubscriptionIdentifier],
    0x11: [t.DATATYPE_UINT32   , "SESSION_EXPIRY_INTERVAL"       , SessionExpiryInterval],
    0x12: [t.DATATYPE_UTF8     , "ASSIGNED CLIENT ID"            , AssignedClientId],
    0x13: [t.DATATYPE_UINT16   , "SERVER KEEPALIVE"              , ServerKeepAlive],
    0x15: [t.DATATYPE_UTF8     , "AUTH METHOD"                   , AuthenticationMethod],
    0x16: [t.DATATYPE_BYTES    , "AUTH DATA"                     , AuthenticationData],
    0x17: [t.DATATYPE_BYTE     , "REQUEST PROBLEM INFO"          , RequestProblemInformation],
    0x18: [t.DATATYPE_UINT32   , "WILL DELAY INTERVAL"           , WillDelayInterval],
    0x19: [t.DATATYPE_BYTE     , "REQUEST RESPONSE INFO"         , RequestResponseInformation],
    0x1A: [t.DATATYPE_UTF8     , "RESPONSE INFO"                 , ResponseInformation],
    0x1C: [t.DATATYPE_UTF8     , "SERVER REFERENCE"              , ServerReference],
    0x1F: [t.DATATYPE_UTF8     , "REASON STRING"                 , ReasonString],
    0x21: [t.DATATYPE_UINT16   , "RECEIVE MAXIMUM"               , ReceiveMaximum],
    0x22: [t.DATATYPE_UINT16   , "TOPIC ALIAS MAXIMUM"           , TopicAliasMaximum],
    0x23: [t.DATATYPE_UINT16   , "TOPIC ALIAS"                   , TopicAlias],
    0x24: [t.DATATYPE_BYTE     , "MAXIMUM QOS"                   , MaximumQos],
    0x25: [t.DATATYPE_BYTE     , "RETAIN AVAILABLE"              , RetainAvailable],
    0x26: [t.DATATYPE_UTF8_PAIR, "USER PROPERTY"                 , UserProperty],
    0x27: [t.DATATYPE_UINT32   , "MAX PACKET SIZE"               , MaximumPacketSize],
    0x28: [t.DATATYPE_BYTE     , "WILDCARD SUBCRIPTION AVAILABLE", WildcardSubscriptionAvailable],
    0x29: [t.DATATYPE_BYTE     , "SUBSCRIPTION ID AVAILABLE"     , SubscriptionIdentifierAvailable],
    0x2A: [t.DATATYPE_BYTE     , "SHARE SUBSCRIPTION AVAILABLE"  , SharedSubscriptionAvailable],
}

def get_property_type(property_id):
    return PROPS_DATA[property_id][PROP_DATA_TYPE]

def get_property_description(property_id):
    return PROPS_DATA[property_id][PROP_DATA_DESC]

def get_property_class(property_id):
    return PROPS_DATA[property_id][PROP_DATA_CLASS]

def get_property_instance(property_id, *args, **kwargs):
    klass = PROPS_DATA[property_id][PROP_DATA_CLASS]

    if klass == NyamukProp:
        return klass(property_id, *args, **kwargs)
    else:
        return klass(*args, **kwargs)

