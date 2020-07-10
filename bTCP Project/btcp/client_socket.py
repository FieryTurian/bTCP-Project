# Onno de Gouw
# Stefan Popa

import struct
import random
import time

from socket import *
from btcp.btcp_socket import BTCPSocket
from btcp.lossy_layer import LossyLayer
from btcp.constants import *


# bTCP client socket
# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close
class BTCPClientSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)
        self._connected = False
        self._window_b = 0
        self._buffer_packets = []
        self._seq_num = 0
        self._ack_num = 0
        self._startTime = 0
        self._counter_packet = 0
        self._counter_ack = 1

    # A method the checks if the received segment has the correct checksum
    def check_cksum(self, segment):
        if self.in_cksum(segment) == 0:
            return True

        return False

    # A method that builds the header for a segment
    def build_header(self, seq_num, ack_num, flags, window, data_length, data):
        header = struct.pack("HHBBhH",
                             seq_num,
                             ack_num,
                             flags,
                             window,
                             data_length,
                             0)

        myChecksum = self.in_cksum(header + data)
        myChecksum = htons(myChecksum) & 0xffff

        header = struct.pack("HHBBhH",
                             seq_num,
                             ack_num,
                             flags,
                             window,
                             data_length,
                             myChecksum)

        return header

    # A method that builds a bTCP segment
    def build_segment(self, seq_num, ack_num, flags, window, data_length, data):
        header = self.build_header(seq_num, ack_num, flags, window, data_length, data)
        segment = header + data

        return segment

    # A method that unpacks the received segment
    def unpack_segment(self, segment):
        header = segment[:HEADER_SIZE]
        data = segment[HEADER_SIZE:]

        seq_num, ack_num, flags, window, data_length, checksum = struct.unpack("HHBBhH", header)

        return seq_num, ack_num, flags, window, data_length, checksum, header, data

    # Called by the lossy layer from another thread whenever a segment arrives.
    def lossy_layer_input(self, segment, address):

        # Timeout: Resend the oldest unacknowledged packet and restart timer
        if (self._startTime + self._timeout - int(round(time.time() * 1000))) > 0 and self._counter_packet < self._window_b\
                and len(self._buffer_packets) > 0:
            self._startTime = int(round(time.time() * 1000))
            self._lossy_layer.send_segment(self._buffer_packets[0])
            self._counter_packet += 1

        # ACK received: Update the unacknowledged packet list and start the timer, if needed
        # Fast Retransmit: If three duplicate ACKs are received, resend the packet that was lost
        if self.check_cksum(segment):
            _, ack_num, flags, temp_window_b, _, _, inp_header, inp_data = self.unpack_segment(segment)

            # The second step of the three-way handshake, when the server send a SYN+ACK segment and the client
            # receives it
            if flags == SYNACK:
                if ack_num == self._seq_num + 1:
                    self._connected = True
                    self._seq_num += 1
                    self._window_b = temp_window_b

            # The second step of the connection termination handshake, when the server send a FIN+ACK segment and the
            # client receives it
            if flags == FINACK:
                self._connected = False

            if flags == ACK:
                if ack_num > self._ack_num:
                    self._counter_ack = 1
                    from_index = self._ack_num
                    self._ack_num = ack_num
                    self._counter_packet = self._window_b - temp_window_b

                    for i in range(from_index, self._ack_num):
                        if len(self._buffer_packets) > 0:
                            self._buffer_packets.pop(0)

                    if len(self._buffer_packets) != 0:
                        self._startTime = int(round(time.time() * 1000))
                    else:
                        self._startTime = 0
                else:
                    if self._ack_num == ack_num:
                        self._counter_ack += 1

                        if self._counter_ack >= 3 and self._counter_packet < self._window_b\
                                and len(self._buffer_packets) > 0:
                            self._lossy_layer.send_segment(self._buffer_packets[0])
                            self._counter_packet += 1

        self._src_address = address

    # Perform a three-way handshake to establish a connection
    def connect(self):
        self._seq_num = random.getrandbits(16)
        segment_packet = self.build_segment(self._seq_num, 0, SYN, self._window_a, 0, struct.pack("d", 0))
        triesCounter = 0
        recv = False

        while triesCounter < self._tries:
            startTime = int(round(time.time() * 1000))
            self._lossy_layer.send_segment(segment_packet)

            while (startTime + self._timeout - int(round(time.time() * 1000))) > 0:
                if self._connected:
                    segment_packet = self.build_header(0, 0, ACK, self._window_a, 0, struct.pack("d", 0))

                    self._lossy_layer.send_segment(segment_packet)
                    self._ack_num = self._seq_num
                    recv = True
                    break

            if not recv:
                triesCounter += 1
            else:
                return 1

        return 0

    # Send data originating from the application in a reliable way to the server
    def send(self, data):
        index = 0
        end = False

        while True:
            # This takes care of the last block of data which may be shorter than PAYLOAD_SIZE
            # and the case when the data is shorter the the PAYLOAD_SIZE
            if self._counter_packet < self._window_b and not end:
                if index + PAYLOAD_SIZE >= len(data):
                    data_packet = data[index:len(data)]
                    end = True
                else:
                    data_packet = data[index:index + PAYLOAD_SIZE]
                    index += PAYLOAD_SIZE

                segment_packet = self.build_segment(self._seq_num, 0, 0, self._window_a, 0, data_packet)
                self._buffer_packets.append(segment_packet)

                # Normal: Send a segment and start timer (if not started yet)
                if self._startTime == 0:
                    self._startTime = int(round(time.time() * 1000))

                self._lossy_layer.send_segment(segment_packet)
                self._counter_packet += 1
                self._seq_num += 1

            if end and len(self._buffer_packets) == 0:
                break

    # Perform a handshake to terminate a connection
    def disconnect(self):
        segment_packet = self.build_segment(self._seq_num, 0, FIN, self._window_a, 0, struct.pack("d", 0))
        triesCounter = 0
        recv = False

        while triesCounter < self._tries:
            startTime = int(round(time.time() * 1000))
            self._lossy_layer.send_segment(segment_packet)

            while (startTime + self._timeout - int(round(time.time() * 1000))) > 0:
                if not self._connected:
                    recv = True
                    break

            if not recv:
                triesCounter += 1
            else:
                break

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
