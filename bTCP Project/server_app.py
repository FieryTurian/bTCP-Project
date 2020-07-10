#!/usr/local/bin/python3

# Onno de Gouw
# Stefan Popa

import argparse
from btcp.server_socket import BTCPServerSocket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
    parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
    parser.add_argument("-o", "--output", help="Where to store the file", default="output.file")
    args = parser.parse_args()

    # Create a bTCP server socket
    s = BTCPServerSocket(args.window, args.timeout)

    # Accept the connection request
    s.accept()

    # Receive data from the client and write it in a file
    file = open(args.output, 'wb')

    data = b""
    new_data = s.recv
    while new_data:
        print("Receiving...")
        data += new_data
        new_data = s.recv
    file.write(data)

    # The full file has been received
    file.close()

    # Clean up any state
    s.close()


main()
