import getopt
import math
import sys
from hashlib import sha3_256
from custom_exceptions import NoNonceException
from socket_class import SocketManager
import random
import threading


class Transaction:
    """
    Class to act as a single transaction.
    """
    def __init__(self, tx_id, tx_data):
        """
        Initialize a simple transaction, oversimplification of transactions represented as strings and IDs.

        Args:
            tx_id(str): The UID of a Transaction represented as a hash of the data.
            tx_data(str): Simplified transaction represented as a string.
        """
        self.tx_id = tx_id
        self.tx_data = tx_data


class MemPool:
    """
    Pool of unconfirmed transactions.
    """
    tx = []

    def get_n_tx(self, number):
        """
        Returns n number of randomly selected unique transactions from the mempool.

        Args:
            number(int): Number of transactions to return

        Returns:
            list[Transaction]: A list of transactions equal to to number requested, if not enough transactions
                exist, return the entire list.
        """
        if number >= len(self.tx):
            return self.tx.copy()
        return_tx = []
        random.seed()
        while len(return_tx) < number:
            transaction = random.choice(self.tx)
            if transaction not in return_tx:
                return_tx.append(transaction)
        return return_tx


class Ledger:
    """
    The block chain.
    """
    block_chain = []


class Block:
    """
    Class to represent one block, used for both the Ledger and for Mining.
    """

    def __init__(self, block_id, previous_block_hash, tx, nonce=None):
        self.block_id = block_id
        self.previous_block_hash = previous_block_hash
        self.tx = tx
        self.block_hash = None
        self.nonce = nonce
        if self.nonce is not None:
            self.block_hash = HashFunctions.hash_block(self)

    def __str__(self):
        """
        Simple string override.

        Returns:
            str: A simple string representing a block, formatted for ease of hashing.

        Raises:
            NoNonceException: Custom exception raised when block has no 'nonce' to prevent invalid blocks being hashed.
        """
        if self.nonce is None:
            raise NoNonceException()
        return_string = "%s\n%s" % (str(self.previous_block_hash), str(self.nonce))
        for transaction in self.tx:
            return_string += "\n%s" % str(transaction)
        return return_string


class HashFunctions:
    """
    Static hashing helper methods.
    """

    @staticmethod
    def hash_block(block):
        hashed = sha3_256(str(block).encode())
        return hashed.hexdigest()


class MiniCoin:
    """
    The MiniCoin Nodes represented as a class.
    """

    DEFAULT_BOOTSTRAP_NODE = "127.0.0.1:5000"
    peers = []

    def __init__(self, port):
        self.ledger = Ledger()
        self.mem_pool = MemPool()
        self.connections = []
        self.port = port
        self.address_string = "127.0.0.1:%s" % str(port)
        self.socket_manager = SocketManager(self, port=port)

    def send_message(self):
        """
        Sends a message over sockets and returns the response.
        """
        pass

    def got_message(self, address, message):
        """
        Callback function for when a message is recieved over sockets.

        Args:
            address: The address of the sender.
            message(str): The message received.

        Returns:
            Some response based on message received.
        """
        pass

    def start_mining(self, block=None):
        """
        Call to start mining for blocks. Kicks off a mining thread.

        Args:
            block(Block): Optional block to begin mining, create a new block if None is provided.

        Returns:
            Block:
                A newly minted block.
        """
        pass

    def __threaded_miner(self, block=None):
        """
        Called by thread, mines a block in a new thread.

        Args:
            block(Block): Optional block to begin mining, create a new block if None is provided.

       Returns:
            Block:
                A newly minted block.
        """
        pass

    def validate_block(self, block):
        """
        Checks validity of a block.

        Args:
            block(Block): New block to be checked.

        Returns:
            bool: True if block is found valid, False otherwise.
        """
        return True

    def announce_transaction(self, transaction):
        """
        Forwards a new Transaction to neighbours.

        Args:
            transaction(Transaction): The new transaction.
        """
        pass


if __name__ == '__main__':
    # Parse CLI arguments
    argv = sys.argv[1:]
    options, arguments = getopt.getopt(argv, "", ["port=", "type="])
    option_dict = {
        "--port": None,
        "--type": None
    }
    for option in options:
        option_dict[option[0]] = option[1]

    # TODO - Delete this, only used for testing atm.
    random.seed()
    while True:
        rand_num = random.random()
        hash_value = HashFunctions.hash_block(rand_num)
        if hash_value[:6] == "00ff00":
            print("Nonce: %s, Hash: %s" % (str(rand_num), hash_value))
