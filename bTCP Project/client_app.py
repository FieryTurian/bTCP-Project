#!/usr/local/bin/python3

# Onno de Gouw
# Stefan Popa

import argparse
from btcp.client_socket import BTCPClientSocket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
    parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
    parser.add_argument("-i", "--input", help="File to send", default="input.file")
    args = parser.parse_args()

    # Create a bTCP client socket with the given window size and timeout value
    s = BTCPClientSocket(args.window, args.timeout)

    # Connect to the server socket
    if s.connect() == 0:
        print("Connection establishment has failed. Please try again.")
    else:
        # Send the given file to the server
        file = open(args.input, 'rb')
        data = file.read()
        print("Sending...")
        s.send(data)

        # The full file has been sent
        print("Done sending.")
        file.close()
        s.disconnect()

        # Clean up any state
        s.close()


main()
