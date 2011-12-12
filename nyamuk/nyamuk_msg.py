import time
from MV import MV

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
        self.direction = MV.DIRECTION_NONE
        self.state = MV.MS_INVALID
        self.dup = False
        self.msg = NyamukMsg()