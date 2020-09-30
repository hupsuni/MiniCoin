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

    def __str__(self):
        return "%s, %s" % (str(self.tx_id), str(self.tx_data))


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
    def __init__(self):
        self.block_chain = []
        # TODO - Add genesis block

    def size(self):
        """
        Simple get length of blockchain.

        Returns:
            int: Length of the blockchain.
        """
        return len(self.block_chain)

    def get_last_block(self):
        """
        Get the most recent block in the ledger.

        Returns:
            Block: The last block in the block chain.block
        """
        return self.block_chain[-1]

    def add_block(self, block):
        """
        Quick check for sequence of block ID, if it matches then append. Does not check for block validity.

        Args:
            block(Block): New block to add.
        """
        if block.block_id == len(self.block_chain):
            self.block_chain.append(block)


class Block:  # TODO - Change self.ledger to MiniCoin.ledger for threading
    """
    Class to represent one block, used for both the Ledger and for Mining.
    """
    TRANSACTIONS_PER_BLOCK = 10

    def __init__(self, block_id, tx, previous_block_hash, nonce=None):
        """
        Init block.

        Args:
            block_id(int): Block number in chain.
            tx(list[Transaction]): List of transactions in block.
            previous_block_hash(str): Hex digest hash of the previous block in chain.
            nonce(float): The nonce for this blocks hash problem.
        """
        self.block_id = block_id
        self.previous_block_hash = previous_block_hash
        if type(tx) is list:
            self.tx = tx
        else:
            self.tx = [tx]
        self.block_hash = None
        self.nonce = nonce
        if self.nonce is not None:
            self.block_hash = HashFunctions.hash_input(self)

    def __str__(self):
        """
        Simple string override. Format of output is new line separated as follows:
        "block_id, block_nonce, previous_block_hash, list of transactions"

        Returns:
            str: A simple string representing a block, formatted for ease of hashing.

        Raises:
            NoNonceException: Custom exception raised when block has no 'nonce' to prevent invalid blocks being hashed.
        """

        if self.nonce is None:
            raise NoNonceException()
        return_string = "%s\n%s\n%s" % (str(self.block_id), str(self.nonce), str(self.previous_block_hash))
        for transaction in self.tx:
            return_string += "\n%s" % str(transaction)
        return return_string

    @staticmethod
    def block_from_string(block_as_string):
        """
        Generates a block from a string in the format of __str__ function.

        Args:
            block_as_string(str): A block represented as output from str(block)

        Returns:
            Block: Reconstructed Block
        """
        parameters = block_as_string.split("\n")
        tx_list = []
        for transaction in parameters[3:]:
            tx_data = transaction.split(", ")
            tx_list.append(Transaction(tx_data[0], tx_data[1]))
        reconstructed_block = Block(int(parameters[0]), tx_list,  parameters[2], nonce=float(parameters[1]))
        return reconstructed_block


class HashFunctions:
    """
    Static hashing helper methods.
    """

    @staticmethod
    def hash_input(block):
        hashed = sha3_256(str(block).encode())
        return hashed.hexdigest()


class MiniCoin:
    """
    The MiniCoin Nodes represented as a class.
    """

    DEFAULT_BOOTSTRAP_NODE = "127.0.0.1:5000"
    HASH_PATTERN = "00ff00"
    ledger_sync = True
    no_new_block = True
    ledger = Ledger()
    mem_pool = MemPool()

    def __init__(self, port):
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
        MiniCoin.no_new_block = True
        # TODO - Add threading
        self.__threaded_miner(block)

    def __threaded_miner(self, block=None):
        """
        Called by thread, mines a block in a new thread.

        Args:
            block(Block): Optional block to begin mining, create a new block if None is provided.

       Returns:
            Block:
                A newly minted block. Returns None if loop is exited without solving the block.
        """
        random.seed()
        # Generate a new block to test random nonce on.
        if block is None:
            mining_block = Block(self.ledger.size(), self.mem_pool.get_n_tx(Block.TRANSACTIONS_PER_BLOCK),
                                 self.ledger.get_last_block().block_hash)
        else:
            mining_block = block
        while MiniCoin.no_new_block and MiniCoin.ledger_sync and mining_block == self.ledger.size():
            # While a block has not been found and node considers its ledger up to date, generate a random nonce,
            # has the mining block and if it conforms to the hash pattern return it, otherwise repeat.
            random_nonce = random.random()
            mining_block.nonce = random_nonce
            block_hash = HashFunctions.hash_input(mining_block)
            if block_hash[0:len(self.HASH_PATTERN)] == self.HASH_PATTERN:
                mining_block.block_hash = block_hash
                self.__announce_minted_block(mining_block)
        return None

    def validate_block(self, block):
        """
        Checks validity of a block.

        Args:
            block(Block): New block to be checked.

        Returns:
            bool: True if block is found valid, False otherwise.
        """
        hash_to_validate = block.block_hash
        current_head_block = self.ledger.get_last_block()
        # All the following requirements must be met for this block to be a valid head of the current ledger.
        if self.ledger.size() > 1 and block.block_id == current_head_block.block_id + 1 and \
                block.previous_block_hash == current_head_block.block_hash and \
                HashFunctions.hash_input(block) == block.block_hash and \
                hash_to_validate[0:len(self.HASH_PATTERN)] == self.HASH_PATTERN:
            return True
        return False

    def announce_transaction(self, transaction):
        """
        Forwards a new Transaction to neighbours.

        Args:
            transaction(Transaction): The new transaction.
        """
        pass

    def propagate_block(self, block):
        pass

    def __announce_minted_block(self, block):
        """
        Verifies block minted by node and appends it to ledger if valid.

        Args:
            block(Block): Freshly minted block
        """
        if self.validate_block(block):
            MiniCoin.no_new_block = False
            self.ledger.add_block(block)


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
        hash_value = HashFunctions.hash_input(rand_num)
        if hash_value[:6] == "00ff00":
            print("Nonce: %s, Hash: %s" % (str(rand_num), hash_value))
