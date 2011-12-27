import time

import nyamuk_const as NC

class NyamukMsg:
    def __init__(self):
        self.mid = 0
        self.topic = None
        self.payload = None
        self.payloadlen = -1
        self.qos = -1
        self.retain = False
        
class NyamukMsgAll:
    
    def __init__(self):
        #next
        self.timestamp = time.time()
        self.direction = NC.DIRECTION_NONE
        self.state = NC.MS_INVALID
        self.dup = False
        self.msg = NyamukMsg()