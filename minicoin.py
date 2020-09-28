import math
from hashlib import sha3_256
from custom_exceptions import NoNonceException


class Transaction:
    pass


class MemPool:
    pass


class Ledger:
    pass


class Block:

    def __init__(self, block_id, previous_block_hash, tx, nonce=None):
        self.block_id = block_id
        self.previous_block_hash = previous_block_hash
        self.tx = tx
        self.block_hash = None
        self.nonce = nonce

    def __str__(self):
        if self.nonce is None:
            raise NoNonceException()
        return_string = "%s\n%s" % (str(self.previous_block_hash), str(self.nonce))
        for transaction in self.tx:
            return_string += "\n%s" % str(transaction)
        return return_string

    @staticmethod
    def hash_block(block):
        hashed = sha3_256(str(block).encode())
        return hashed.hexdigest()


class MiniCoin:

    DEFAULT_BOOTSTRAP_NODE = "127.0.0.1:5000"

    def __init__(self):
        self.ledger = Ledger()
        self.mem_pool = MemPool()
        self.connections = []


if __name__ == '__main__':
    for i in range(0, 99999999):
        hash_value = Block.hash_block(i)
        if hash_value[:6] == "00ff00":
            print("Block ID: %s, Hash: %s" % (str(i), hash_value))
