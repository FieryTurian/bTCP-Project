# Onno de Gouw
# Stefan Popa

import socket
import select
import threading
from btcp.constants import *


# Continuously read from the socket and whenever a segment arrives,
# call the lossy_layer_input method of the associated socket. 
# When flagged, return from the function.
def handle_incoming_segments(bTCP_sock, event, udp_sock):
    while not event.is_set():
        # We do not block here, because we might never check the loop condition in that case
        rlist, wlist, elist = select.select([udp_sock], [], [], 1)
        if rlist:
            segment, address = udp_sock.recvfrom(SEGMENT_SIZE)
            bTCP_sock.lossy_layer_input(segment, address)


# The lossy layer emulates the network layer in that it provides bTCP with 
# an unreliable segment delivery service between a and b. When the lossy layer is created, 
# a thread is started that calls handle_incoming_segments. 
class LossyLayer:
    def __init__(self, bTCP_sock, a_ip, a_port, b_ip, b_port):
        self._bTCP_sock = bTCP_sock
        self._b_ip = b_ip
        self._b_port = b_port
        self._udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._udp_sock.bind((a_ip, a_port))
        self._event = threading.Event()
        self._thread = threading.Thread(target=handle_incoming_segments,
                                        args=(self._bTCP_sock, self._event, self._udp_sock))
        self._thread.start()

    # Flag the thread that it can stop and close the socket.
    def destroy(self):
        self._event.set()
        self._thread.join()
        self._udp_sock.close()

    # Put the segment into the network
    def send_segment(self, segment):
        self._udp_sock.sendto(segment, (self._b_ip, self._b_port))
