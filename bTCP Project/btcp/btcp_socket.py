# Onno de Gouw
# Stefan Popa

class BTCPSocket:
    def __init__(self, window, timeout):
        self._window_a = window
        self._timeout = timeout
        self._tries = 10
   
    # Return the Internet checksum of data
    @staticmethod
    def in_cksum(data):
        # If the length of data is not a multiple of 16-bit words, then pad with one byte of zeros.

        data = bytearray(data)
        cksum = 0
        countTo = (len(data) // 2) * 2

        for count in range(0, countTo, 2):
            value = data[count + 1] * 256 + data[count]
            cksum = cksum + value
            cksum = cksum & 0xffffffff

        if countTo < len(data):
            cksum = cksum + data[-1]
            cksum = cksum & 0xffffffff

        cksum = (cksum >> 16) + (cksum & 0xffff)
        cksum = cksum + (cksum >> 16)
        checksum = ~cksum
        checksum = checksum & 0xffff
        checksum = checksum >> 8 | (checksum << 8 & 0xff00)

        return checksum