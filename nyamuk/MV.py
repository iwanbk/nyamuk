'''
@author Iwan Budi Kusnanto
'''
class MV:
    '''
    MQTT Variable and Constanta
    '''
    UNKNOWN_VAL = -1
    
    PROTOCOL_NAME = "MQIsdp"
    PROTOCOL_VERSION = 3
    
    CONNECT = 0x10
    
    #CLIENT_STATE
    CS_NEW = 0
    CS_CONNECTED = 1
    CS_DISCONNECTED = 2
    
    #socket
    INVALID_SOCKET = -1
    KEEPALIVE_VAL = 60

    #ERROR
    ERR_SUCCESS = 0
    ERR_PAYLOAD_SIZE = 9
    #
    MESSAGE_RETRY = 20
    
    def __init__(self):
        pass
    