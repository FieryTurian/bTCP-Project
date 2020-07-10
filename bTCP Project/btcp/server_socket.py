# Onno de Gouw
# Stefan Popa

import struct
import random

from socket import *
from btcp.lossy_layer import LossyLayer
from btcp.btcp_socket import BTCPSocket
from btcp.constants import *


# The bTCP server socket
# A server application makes use of the services provided by bTCP by calling accept, recv, and close
class BTCPServerSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT)
        self._connected = False
        self._window_b = 0
        self._buffer_packets = []
        self._seq_num = 0

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

    # Called by the lossy layer from another thread whenever a segment arrives
    def lossy_layer_input(self, segment, address):
        recv = False

        # Normal: If correct segment arrives, send and ACK for the segment
        if self.check_cksum(segment):
            seq_num_x_1, _, flags_1, self._window_b, _, _, inp_header_1, inp_data_1 = self.unpack_segment(segment)

            # Handshake: SYN flag received
            if flags_1 == SYN:
                recv = True
                self._connected = True
                self._seq_num = seq_num_x_1 + 1

                seq_num_y = random.getrandbits(16)
                segment_packet = self.build_segment(seq_num_y, self._seq_num, SYNACK, self._window_a, 0, struct.pack("d", 0))

                self._lossy_layer.send_segment(segment_packet)

            # Handshake: If the segment with the ACK flag set in the three way handshake was received, simply
            # drop this segment
            if flags_1 == ACK:
                recv = True

            # Connection termination: FIN flag received
            if flags_1 == FIN:
                segment_packet = self.build_segment(0, self._seq_num + 1, FINACK, self._window_a, 0, struct.pack("d", 0))

                self._lossy_layer.send_segment(segment_packet)
                recv = True
                self._connected = False

            if seq_num_x_1 == self._seq_num:
                segment_packet = self.build_segment(0, self._seq_num + 1, ACK, self._window_a - len(self._buffer_packets) - 1,
                                                    0, struct.pack("d", 0))

                self._lossy_layer.send_segment(segment_packet)
                self._seq_num += 1
                recv = True

                self._buffer_packets.append(inp_data_1)

        # Previously received segment/ checksum check fail segment / Out-of-order segment:
        # Fast Retransmit process start / Send an ACK and drop packet
        if not recv and self._connected:
            segment_packet = self.build_segment(0, self._seq_num, ACK, self._window_a - len(self._buffer_packets),
                                                0, struct.pack("d", 0))

            self._lossy_layer.send_segment(segment_packet)

        self._src_adress = address

    # Wait for the client to initiate a three-way handshake
    def accept(self):
        while True:
            if self._connected:
                break

    # Send any incoming data to the application layer
    @property
    def recv(self):
        while True:
            if len(self._buffer_packets) != 0:
                inp_data = self._buffer_packets.pop(0)

                if self._connected:
                    return inp_data

                return

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()