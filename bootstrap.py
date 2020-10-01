import time

from socket_class import SocketManager
import random
import threading


class BootStrap:
    """
    Bootstrap node for managing new connections.
    """
    DEFAULT_BOOTSTRAP_NODE = "127.0.0.1:5000"
    REFRESH_RATE = 100
    node_list = []

    def __init__(self, bootstrap_address_string=DEFAULT_BOOTSTRAP_NODE):
        address = bootstrap_address_string.split(":")
        ip = address[0]
        port = int(address[1])
        self.socket_manager = SocketManager(self, ip=ip, port=port)

    def start_server(self):
        self.run()
        threading.Thread(target=self.__check_for_dead_connections).start()

    def __check_for_dead_connections(self):
        while SocketManager.run:
            time.sleep(BootStrap.REFRESH_RATE)
            print("Checking for dead connections...")
            for address in BootStrap.node_list:
                address_details = address.split(":")
                response = self.socket_manager.send_message(address_details[0], int(address_details[1]), "alive?")
                if response != "True":
                    print("Node: %s found dead, removing...")
                    BootStrap.node_list.remove(address)

    def stop_server(self):
        self.socket_manager.stop_server()

    def run(self):
        self.socket_manager.listen()

    def got_message(self, address, message):
        ret_message = "None"
        message_csv = message.split(SocketManager.MESSAGE_SEPARATOR_PATTERN)
        if message_csv[0] == "connect" or message_csv[0] == "client connect":
            num_connections = int(message_csv[2])
            if len(BootStrap.node_list) <= num_connections:
                connection_list = BootStrap.node_list.copy()
            else:
                random.seed()
                index = random.randint(0, len(BootStrap.node_list))
                connection_list = []
                skip = 0
                for i in range(0, num_connections):
                    selected_node_index = (index + skip + i) % len(BootStrap.node_list)
                    if BootStrap.node_list[selected_node_index] != "127.0.0.1:%s" % message[1]:
                        connection_list.append(BootStrap.node_list[selected_node_index])
                    else:
                        skip += 1
                        i -= 1
                        if skip > 5:
                            break
            ret_message = "nodes"
            for details in connection_list:
                ret_message += SocketManager.MESSAGE_SEPARATOR_PATTERN + str(details)
            address_string = str(address[0]) + ":" + str(message_csv[1])
            if address_string not in BootStrap.node_list and message_csv != "client connect":
                BootStrap.node_list.append(address_string)
                print("New connection from: %s" % str(address_string))
        return ret_message

    def get_node_list(self):
        ret_message = ""
        for node in BootStrap.node_list:
            ret_message += str(node) + "\n"
        return ret_message
