import math
from hashlib import sha3_256
from custom_exceptions import NoNonceException
from socket_class import SocketManager
import random


class Transaction:
    pass


class MemPool:
    tx = []


class Ledger:
    block_chain = []


class Block:

    def __init__(self, block_id, previous_block_hash, tx, nonce=None):
        self.block_id = block_id
        self.previous_block_hash = previous_block_hash
        self.tx = tx
        self.block_hash = None
        self.nonce = nonce
        if self.nonce is not None:
            self.block_hash = Block.hash_block(self)

    def __str__(self):
        if self.nonce is None:
            raise NoNonceException()
        return_string = "%s\n%s" % (str(self.previous_block_hash), str(self.nonce))
        for transaction in self.tx:
            return_string += "\n%s" % str(transaction)
        return return_string

    @staticmethod  # TODO - Move this from block class
    def hash_block(block):
        hashed = sha3_256(str(block).encode())
        return hashed.hexdigest()


class MiniCoin:

    DEFAULT_BOOTSTRAP_NODE = "127.0.0.1:5000"
    peers = []

    def __init__(self, port):
        self.ledger = Ledger()
        self.mem_pool = MemPool()
        self.connections = []
        self.port = port
        self.socket_manager = SocketManager(self, port=port)

    def send_message(self):
        pass

    def got_message(self, address, message):
        pass


if __name__ == '__main__':
    # numbers = []
    # for i in range(0, 99999999):
    #     numbers.append(i)
    random.seed()
    while True:
        rand_num = random.random()
        hash_value = Block.hash_block(rand_num)
        if hash_value[:6] == "00ff00":
            print("Nonce: %s, Hash: %s" % (str(rand_num), hash_value))
