"""
This class is derived from my older code and has been modified to suit this assignment.
-Nick Huppert, s3729119
"""

import socket
import threading
from time import sleep


class SocketManager:
    DEFAULT_IP = "127.0.0.1"
    DEFAULT_PORT = 5000
    DEFAULT_PACKET_SIZE = 4096
    DEFAULT_IDLE_TIMEOUT = 30
    run = True

    def __init__(self, callback, ip=DEFAULT_IP, port=DEFAULT_PORT, packet_size=DEFAULT_PACKET_SIZE,
                 timeout=DEFAULT_IDLE_TIMEOUT, server=True):
        self.__host_ip = ip
        self.__host_port = port
        self.__packet_size = packet_size
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if server:
            self.socket.bind((self.__host_ip, self.__host_port))
        self.__timeout = timeout
        self.callback = callback

    def listen(self):
        """
        Starts the socket server listening for connections in new thread.
        Each connection is dispatched to a new thread.
        """
        SocketManager.run = True
        self.socket.listen()
        threading.Thread(target=self.__listen_loop).start()
        print("Now listening on port: %s" % self.__host_port)

    def __listen_loop(self):
        try:

            while SocketManager.run is True:
                self.socket.settimeout(self.__timeout)
                try:
                    client, address = self.socket.accept()
                    client.settimeout(self.__timeout)
                    threading.Thread(target=self.__server_action, args=(client, address)).start()
                except socket.timeout:
                    pass
        except threading.ThreadError:
            pass
        finally:
            self.socket.close()

    # Parse the message received from a client and call appropriate function
    def __server_action(self, client, address):
        """
        Args:
            client: The client who has connected to the server
            address: The address of the client
        """
        response = ""
        try:
            with client:
                while True:
                    message = client.recv(self.__packet_size)
                    if message == b'':
                        break
                    if message is not None:
                        response = str(self.callback.got_message(address, message.decode()))
                        # message_csv = message.decode().split(",")
                        client.sendall(response.encode())
                        break
                    else:
                        break

        except (TimeoutError, AttributeError, socket.timeout) as e:
            print("%s" % e)
        finally:
            client.close()

    def send_message(self, ip, port, message):
        """
        Takes a string message and sends it to remote server, returning the response.

        Args:
            message(str): The message to send, encrypted, to the remote server.

        Returns:
            str: The response of the server, decrypted, or None on error.
         """
        socket_connection = None
        try:
            socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            response = None
            socket_connection.connect((ip, int(port)))
            socket_connection.sendall(message.encode())
            sleep(.1)
            while response is None:
                response = socket_connection.recv(self.__packet_size)
            socket_connection.close()
            return response.decode()
        except (ConnectionRefusedError, AttributeError, socket.timeout, ConnectionError) as e:
            print("%s" % e)
            return_value = None
        finally:
            socket_connection.close()
        return return_value
