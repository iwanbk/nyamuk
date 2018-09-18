#!/usr/bin/env python
# -*- coding: utf8 -*-

# reason codes
REASON_SUCCESS                = 0x00
REASON_NORMAL_DISCONN         = 0x00
REASON_GRANTED_QOS0           = 0x00
REASON_GRANTED_QOS1           = 0x01
REASON_GRANTED_QOS2           = 0x02
REASON_DISCONN_W_WILL_MSG     = 0x04
REASON_NO_MATCH_SUBSCRIBERS   = 0x10
REASON_NO_SUBSCRIPTION        = 0x11
REASON_CONTINUE_AUTH          = 0x18
REASON_REAUTH                 = 0x19
REASON_UNSPECIFIED_ERR        = 0x80
REASON_BAD_PKT                = 0x81
REASON_PROTOCOL_ERR           = 0x82
REASON_IMPL_ERR               = 0x83
REASON_UNSUP_PROTOCOL_VERS    = 0x84
REASON_INVALID_CLIENT_ID      = 0x85
REASON_BAD_USERNAME_OR_PWD    = 0x86
REASON_NOT_AUTHORIZED         = 0x87
REASON_SERVER_UNAVAIL         = 0x88
REASON_SERVER_BUSY            = 0x89
REASON_BANNED                 = 0x8A
REASON_SERVER_SHUTTING_DOWN   = 0x8B
REASON_BAD_AUTH_METHOD        = 0x8C
REASON_KEEPALIVE_TIMEOUT      = 0x8D
REASON_SESS_TAKEN_OVER        = 0x8E
REASON_INVALID_TOPIC_FILTER   = 0x8F
REASON_INVALID_TOPIC_NAME     = 0x90
REASON_PACKET_ID_IN_USE       = 0x91
REASON_PACKET_ID_NOT_FOUND    = 0x92
REASON_RECV_MAX_EXCEEDED      = 0x93
REASON_INVALID_TOPIC_ALIAS    = 0x94
REASON_PACKET_TOO_LARGE       = 0x95
REASON_MSG_RATE_TOO_HIGH      = 0x96
REASON_QUOTA_EXCEEDED         = 0x97
REASON_ADMIN_ACTION           = 0x98
REASON_INVALID_PAYLOAD_FMT    = 0x99
REASON_UNSUP_RETAIN           = 0x9A
REASON_UNSUP_QOS              = 0x9B
REASON_USE_ANOTHER_SERVER     = 0x0C
REASON_SERVER_MOVED           = 0x9D
REASON_UNSUP_SHARED_SUBSCRS   = 0x9E
REASON_CONN_RATE_EXCEEDED     = 0x9F
REASON_MAX_CONNECT_TIME       = 0xA0
REASON_UNSUP_SUBSCR_IDS       = 0xA1
REASON_UNSUP_WILDCARD_SUBSCRS = 0xA2


REASON_DATA_NAME = 0

REASON_DATA = {
    # success exact message depend on the contexgt
    REASON_SUCCESS                : ["Success / Normal disconnection / Granted QoS 0"],
    REASON_GRANTED_QOS1           : ["Granted QoS 1"],
    REASON_GRANTED_QOS2           : ["Granted Qos 2"],
    REASON_DISCONN_W_WILL_MSG     : ["Disconnect with Will Message"],
    REASON_NO_MATCH_SUBSCRIBERS   : ["No matching subscribers"],
    REASON_NO_SUBSCRIPTION        : ["No subscription existed"],
    REASON_CONTINUE_AUTH          : ["Continue authentication"],
    REASON_REAUTH                 : ["Re-authenticate"],
    REASON_UNSPECIFIED_ERR        : ["Unspecified error"],
    REASON_BAD_PKT                : ["Malformed Packet"],
    REASON_PROTOCOL_ERR           : ["Protocol error"],
    REASON_IMPL_ERR               : ["Implementation specific error"],
    REASON_UNSUP_PROTOCOL_VERS    : ["Unsupported Protocol Version"],
    REASON_INVALID_CLIENT_ID      : ["Client Identifier not valid"],
    REASON_BAD_USERNAME_OR_PWD    : ["Bad Username or password"],
    REASON_NOT_AUTHORIZED         : ["Not authorized"],
    REASON_SERVER_UNAVAIL         : ["Server unavailable"],
    REASON_SERVER_BUSY            : ["Server busy"],
    REASON_BANNED                 : ["Banned"],
    REASON_SERVER_SHUTTING_DOWN   : ["Server shutting down"],
    REASON_BAD_AUTH_METHOD        : ["Bad authentication method"],
    REASON_KEEPALIVE_TIMEOUT      : ["Keep Alive timeout"],
    # clientID already used by another connection
    REASON_SESS_TAKEN_OVER        : ["Session take over"],
    REASON_INVALID_TOPIC_FILTER   : ["Topic Filter is invalid"],
    REASON_INVALID_TOPIC_NAME     : ["Topic Name is invalid"],
    REASON_PACKET_ID_IN_USE       : ["Packet identifier in use"],
    REASON_PACKET_ID_NOT_FOUND    : ["Packet identifier not found"],
    # client or server received more that "Receive Maximum" publication for which
    # it has not send PUBACK or PUBCOMP
    REASON_RECV_MAX_EXCEEDED      : ["Receive Maximum exceeded"],
    REASON_INVALID_TOPIC_ALIAS    : ["Topic Alias is invalid"],
    REASON_PACKET_TOO_LARGE       : ["Packet too large"],
    REASON_MSG_RATE_TOO_HIGH      : ["Message rate too high"],
    REASON_QUOTA_EXCEEDED         : ["Quota Exceeded"],
    REASON_ADMIN_ACTION           : ["Administrative action"],
    REASON_INVALID_PAYLOAD_FMT    : ["Payload format invalid"],
    REASON_UNSUP_RETAIN           : ["Retain not supported"],
    REASON_UNSUP_QOS              : ["QoS not supported"],
    REASON_USE_ANOTHER_SERVER     : ["Use another server"],
    REASON_SERVER_MOVED           : ["Server moved"],
    REASON_UNSUP_SHARED_SUBSCRS   : ["Shared Subscriptions not supported"],
    REASON_CONN_RATE_EXCEEDED     : ["Connection rate exceeded"],
    REASON_MAX_CONNECT_TIME       : ["Maximum connect time"],
    REASON_UNSUP_SUBSCR_IDS       : ["Subscription Identifiers not supported"],
    REASON_UNSUP_WILDCARD_SUBSCRS : ["Wildcard Subscriptions not supported"],
}

def get_reason_name(reason):
    return REASON_DATA[reason][REASON_DATA_NAME]
