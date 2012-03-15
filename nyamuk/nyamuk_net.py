import socket
import errno

import nyamuk_const as NC

def MOSQ_MSB(A):
    return (( A & 0xFF00) >> 8)
    
def MOSQ_LSB(A):
    return (A & 0x00FF)

def connect(sock, addr):
    try:
        ret = sock.connect(addr)
    except socket.error as (errno, str):
        print "socket.error. Errno = ", errno, " err msg = ", str
        return -1, errno
    except socket.herror as (errno, str):
        print "socket.error. Errno = ", errno, " err msg = ", str
        return -1, errno
    except socket.gaierror as (errno,str):
        print "socket.error. Errno = ", errno, " err msg = ", str
        return -1, errno
    except socket.timeout:
        return -1, errno.ETIMEDOUT
    
    return 0
    
def read(sock, count):
    """Read count byte from socket."""
    try:
        str = sock.recv(count)
    except socket.error as (errno, str):
        print "socket.error. Errno = ", errno, " err msg = ", str
        return -1, errno
    except socket.herror as (errno, str):
        print "socket.error. Errno = ", errno, " err msg = ", str
        return -1, errno
    except socket.gaierror as (errno,str):
        print "socket.error. Errno = ", errno, " err msg = ", str
        return -1, errno
    except socket.timeout:
        return -1, errno.ETIMEDOUT
    
    ba = bytearray(str)
    return ba, None

def write(sock, payload):
    """Write payload to socket."""
    try:
        len = sock.send(payload)
    except socket.error as (errno, str):
        print "socket.error. Errno = ", errno, " err msg = ", str
        return -1, errno
    except socket.herror as (errno, str):
        print "socket.herror. Errno = ", errno, " err msg = ", str
        return -1, errno
    except socket.gaierror as (errno,str):
        print "socket.gaierror. Errno = ", errno, " err msg = ", str
        return -1, errno
    except socket.timeout:
        return -1, errno.ETIMEDOUT
    
    return len, None

def setkeepalives(sock):
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE,1)