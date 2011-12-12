import socket

def MOSQ_MSB(A):
    return (( A & 0xFF00) >> 8)
    
def MOSQ_LSB(A):
    return (A & 0x00FF)

def read(sock, count):
    str = sock.recv(count)
    ba = bytearray(str)
    return len(ba),ba, None

def write(sock, payload):
    len = sock.send(payload)
    return None, len