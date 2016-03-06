
TYPE_ACK = 0b1010101010101010
TYPE_DATA = 0b0101010101010101
TYPE_EOF = 0b1111000011110000


#data = "45 00 00 47 73 88 40 00 40 06 a2 c4 83 9f 0e 85 83 9f 0e a1"

def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

def generateChecksum(datachunk):
    s = 0
    for i in range(1, len(datachunk), 2):
        w = ord(datachunk[i-1]) + (ord(datachunk[i]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff

def check_checksum(data,checksum):
    new_checksum = generateChecksum(data)
    error = new_checksum +checksum
    if error:
        print ("Error detected !!!  ")
        return 0
    return 1