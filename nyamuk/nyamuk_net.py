def MOSQ_MSB(A):
    return (( A & 0xFF00) >> 8)
    
def MOSQ_LSB(A):
    return (A & 0x00FF)