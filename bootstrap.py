from socket_class import SocketManager
import random


class BootStrap:
    """
    Bootstrap node for managing new connections
    """
    DEFAULT_BOOTSTRAP_NODE = "127.0.0.1:5000"

    def __init__(self, bootstrap_address_string=DEFAULT_BOOTSTRAP_NODE):
        address = bootstrap_address_string.split(":")
        ip = address[0]
        port = int(address[1])
        self.socket_manager = SocketManager(self, ip=ip, port=port)
        self.node_list = []

    def run(self):
        self.socket_manager.listen()

    def got_message(self, address, message):
        ret_message = "None"
        message_csv = message.split(",")
        if message_csv[0] == "connect":
            if len(self.node_list) != 0:
                ret_message = str(random.choice(self.node_list))
            if address not in self.node_list:
                self.node_list.append(str(address[0]) + ":" + str(message_csv[1]))
                print("New connection from: %s" % str(address))
        elif message_csv[0] == "client connect":
            ret_message = str(random.choice(self.node_list))
        return ret_message

    def get_node_list(self):
        ret_message = ""
        for node in self.node_list:
            ret_message += str(node) + "\n"
        return ret_message
