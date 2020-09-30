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

    def start_server(self):
        self.run()

    def stop_server(self):
        self.socket_manager.stop_server()

    def run(self):
        self.socket_manager.listen()

    def got_message(self, address, message):
        print(message)
        ret_message = "None"
        message_csv = message.split(SocketManager.MESSAGE_SEPARATOR_PATTERN)
        if message_csv[0] == "connect" or message_csv[0] == "client connect":
            num_connections = int(message_csv[2])
            if len(self.node_list) <= num_connections:
                connection_list = self.node_list.copy()
            else:
                random.seed()
                index = random.randint(0, len(self.node_list))
                connection_list = []
                for i in range(0, num_connections):
                    selected_node_index = (index + i) % len(self.node_list)
                    connection_list.append(self.node_list[selected_node_index])
            ret_message = "nodes"
            for details in connection_list:
                ret_message += SocketManager.MESSAGE_SEPARATOR_PATTERN + str(details)

            if address not in self.node_list and message_csv != "client connect":
                self.node_list.append(str(address[0]) + ":" + str(message_csv[1]))
                print("New connection from: %s" % str(address))
        return ret_message

    def get_node_list(self):
        ret_message = ""
        for node in self.node_list:
            ret_message += str(node) + "\n"
        return ret_message
