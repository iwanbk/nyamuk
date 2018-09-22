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
    def __init__(self, tipe, props=[]):
        self.type = tipe
        self.props = props

class EventConnack(BaseEvent):
    """CONNACK received."""
    def __init__(self, reason, session_present=0, props=[]):
        BaseEvent.__init__(self, NC.CMD_CONNACK, props=props)
        # deprecated
        self.ret_code = reason
        #NOTE: in v5, retcode field is renamed reason
        self.reason   = reason
        # >= v3.1.1 only
        self.session_present = session_present

class EventPublish(BaseEvent):
    """PUBLISH received."""
    def __init__(self, msg, props=[]):
        BaseEvent.__init__(self, NC.CMD_PUBLISH, props=props)
        self.msg = msg

class EventSuback(BaseEvent):
    """SUBACK received."""
    def __init__(self, mid, reasons, props=[]):
        BaseEvent.__init__(self, NC.CMD_SUBACK, props=props)
        self.mid     = mid
        self.reasons = reasons
        # deprecated
        self.granted_qos = reasons

    def __str__(self):
        return "SUBACK(mid={0}, reasons={1}, props={2})".\
            format(self.mid, self.reasons, self.props)

class EventUnsuback(BaseEvent):
    """UNSUBACK received."""
    def __init__(self, mid, props=[]):
        BaseEvent.__init__(self, NC.CMD_UNSUBACK, props=props)
        self.mid = mid

class EventPuback(BaseEvent):
    """PUBACK received."""
    def __init__(self, mid, reason=None, props=[]):
        BaseEvent.__init__(self, NC.CMD_PUBACK, props=props)
        self.mid    = mid
        # v5 only
        self.reason = reason

class EventPubrec(BaseEvent):
    """PUBREC received."""
    def __init__(self, mid):
        BaseEvent.__init__(self, NC.CMD_PUBREC)
        self.mid = mid

class EventPubrel(BaseEvent):
    """PUBREL received."""
    def __init__(self, mid):
        BaseEvent.__init__(self, NC.CMD_PUBREL)
        self.mid = mid

class EventPubcomp(BaseEvent):
    """PUBCOMP received."""
    def __init__(self, mid):
        BaseEvent.__init__(self, NC.CMD_PUBCOMP)
        self.mid = mid

class EventNeterr(BaseEvent):
    """Network error event."""
    def __init__(self, errnum, msg):
        BaseEvent.__init__(self, EV_NET_ERR)
        self.errnum = errnum
        self.msg = msg

class EventPingResp(BaseEvent):
    """PINGRESP received."""
    def __init__(self):
        BaseEvent.__init__(self, NC.CMD_PINGRESP)

class EventDisconnect(BaseEvent):
    """DISCONNECT message received."""
    def __init__(self, reason, props=[]):
        BaseEvent.__init__(self, NC.CMD_DISCONNECT, props=props)

        self.reason = reason
