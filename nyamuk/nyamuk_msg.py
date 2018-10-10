"""
Copyright(c)2012 Iwan Budi Kusnanto
"""
import time

import nyamuk_const as NC

class NyamukMsg(object):
    """Nyamuk message."""
    def __init__(self, topic=None, payload=None, qos=-1, retain=False):
        self.mid = 0
        self.topic = topic
        self.payload = payload
        self.payloadlen = -1 if payload is None else len(payload)
        self.qos = qos
        self.retain = retain

    def __str__(self):
        return "Msg(mid={mid}, topic={topic}, msg={msg}, qos={qos})".\
            format(mid=self.mid, topic=self.topic, msg=self.payload, qos=self.qos)

class NyamukMsgAll(object):
    def __init__(self):
        #next
        self.timestamp = time.time()
        self.direction = NC.DIRECTION_NONE
        self.state = NC.MS_INVALID
        self.dup = False
        self.msg = NyamukMsg()

class NyamukWillMsg(NyamukMsg):
    """Will message has specific properties (in CONNECT packet)"""
    def __init__(self, topic=None, payload=None, qos=-1, retain=False, props=[]):
        super(NyamukWillMsg, self).__init__(topic, payload, qos, retain)
        self.props = props

    def __str__(self):
        return "WillMsg(mid={mid}, topic={topic}, msg={msg}, qos={qos})".\
            format(mid=self.mid, topic=self.topic, msg=self.payload, qos=self.qos)


