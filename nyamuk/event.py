"""Nyamuk event."""
import socket

import nyamuk_const as NC

#mqtt event
EV_CONNACK = NC.CMD_CONNACK
EV_PUBLISH = NC.CMD_PUBLISH
EV_SUBACK = NC.CMD_SUBACK

#non mqtt event
EV_NET_ERR = 1000

class BaseEvent:
    """Event Base Class."""
    def __init__(self, tipe):
        self.type = tipe

class EventConnack(BaseEvent):
    """CONNACK received."""
    def __init__(self, ret_code):
        BaseEvent.__init__(self, NC.CMD_CONNACK)
        self.ret_code = ret_code

class EventPublish(BaseEvent):
    """PUBLISH received."""
    def __init__(self, msg):
        BaseEvent.__init__(self, NC.CMD_PUBLISH)
        self.msg = msg

class EventSuback(BaseEvent):
    """SUBACK received."""
    def __init__(self, mid, granted_qos):
        BaseEvent.__init__(self, NC.CMD_SUBACK)
        self.mid = mid
        self.granted_qos = granted_qos

class EventNeterr(BaseEvent):
    """Network error event."""
    def __init__(self, errnum, msg):
        BaseEvent.__init__(self, EV_NET_ERR)
        self.errnum = errnum
        self.msg = msg