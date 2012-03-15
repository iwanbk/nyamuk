import nyamuk_const as NC
class BaseEvent:
    def __init__(self, type):
        self.type = type

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
