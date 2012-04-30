"""
Nyamuk networking module.
Copyright(c) 2012 Iwan Budi Kusnanto
"""
import socket
import errno

def MOSQ_MSB(A):
    """get most significant byte."""
    return (( A & 0xFF00) >> 8)
    
def MOSQ_LSB(A):
    """get less significant byte."""
    return (A & 0x00FF)

def connect(sock, addr):
    """Connect to some addr."""
    try:
        sock.connect(addr)
    except socket.error as (_, msg):
        return (socket.error, msg)
    except socket.herror as (_, msg):
        return (socket.herror, str)
    except socket.gaierror as (_, msg):
        return (socket.gaierror, msg)
    except socket.timeout:
        return (socket.timeout, "timeout")
    
    return None
    
def read(sock, count):
    """Read from socket and return it's byte array representation.
    count = number of bytes to read
    """
    try:
        data = sock.recv(count)
    except socket.error as (errnum, errmsg):
        return data, errnum, errmsg
    except socket.herror as (errnum, errmsg):
        return data, errnum, errmsg
    except socket.gaierror as (errnum, errmsg):
        return data, errnum, errmsg
    except socket.timeout:
        return data, errno.ETIMEDOUT, "Connection timed out"
    
    ba_data = bytearray(data)
    
    if len(ba_data) == 0:
        return ba_data, 0, "Connection closed"
    
    return ba_data, 0, ""

def write(sock, payload):
    """Write payload to socket."""
    try:
        length = sock.send(payload)
    except socket.error as (_, msg):
        return -1, (socket.error, msg)
    except socket.herror as (_, msg):
        return -1, (socket.error, msg)
    except socket.gaierror as (_, msg):
        return -1, (socket.gaierror, msg)
    except socket.timeout:
        return -1, (socket.timeout, "timeout")
    
    return length, None

def setkeepalives(sock):
    """set sock to be keepalive socket."""
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)