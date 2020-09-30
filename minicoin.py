import getopt
import math
import sys
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
import time
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

    def __eq__(self, other):
        if type(other) == type(self):
            if self.tx_id == other.tx_id and self.tx_data == other.tx_data:
                return True
        return False

    @staticmethod
    def transaction_from_string(transaction_string):
        split_tx_string = transaction_string.split(", ")
        return Transaction(split_tx_string[0], split_tx_string[1])


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

    def add_tx(self, tx):
        """
        Adds a list of transactions to the mem pool, supports single transactions.
        Args:
            tx: List of Transactions.

        """
        transaction_is_new = False
        if type(tx) is Transaction:
            tx_list = [tx]
        elif type(tx) is list:
            tx_list = tx
        else:
            return transaction_is_new
        for transaction in tx_list:
            if transaction not in self.tx:
                self.tx.append(transaction)
                transaction_is_new = True
        return transaction_is_new

    def purge_confirmed_tx(self, tx):
        """
        Removes a list of transactions from the mem pool, supports single transactions.

        Args:
            tx: List of Transactions.

        """
        if type(tx) is Transaction:
            tx_list = [tx]
        elif type(tx) is list:
            tx_list = tx
        else:
            return False
        for transaction in tx_list:
            if transaction in self.tx:
                self.tx.remove(transaction)


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

    def get_genesis_block(self):
        """
        Returns the first block in the blockchain, known as the genesis block.

        Returns:
            Block: First block in the blockchain, known as the genesis block.
        """
        return self.block_chain[0]

    def __str__(self):
        return_string = "LEDGER:"
        for block in self.block_chain:
            return_string += "BLOCK:" + str(block)
        return_string += "BLOCK:LEDGER:"
        return return_string

    @staticmethod
    def ledger_from_string(ledger_string):
        ledger_list = []
        ledger_array = ledger_string.split("BLOCK:")
        if ledger_array[0] == "LEDGER:" and ledger_array[-1] == "LEDGER:":
            for block in ledger_array[1:-1]:
                ledger_list.append(Block.block_from_string(block))
        return ledger_array.copy()

    def replace_blockchain(self, block_chain):
        if len(block_chain) > len(self.block_chain):
            self.block_chain = block_chain.copy()


class Block:
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
        reconstructed_block = Block(int(parameters[0]), tx_list, parameters[2], nonce=float(parameters[1]))
        return reconstructed_block


class HashFunctions:
    """
    Static hashing helper methods.
    """
    # Average time to mine based on 20 random attempts on genesis block: 422768.05 microseconds.

    @staticmethod
    def hash_input(hash_me):
        """
        Returns the hash of any object that responds to the __str__ function.

        Args:
            hash_me: The object to be hashed.

        Returns:
            str: The hex digest of the hash of the given item.
        """
        hashed = sha3_256(str(hash_me).encode())
        return hashed.hexdigest()


class MiniCoin:
    """
    The MiniCoin Nodes represented as a class.
    """

    DEFAULT_BOOTSTRAP_NODE = "127.0.0.1:5000"
    HASH_PATTERN = "00ff00"
    MAX_CONNECTIONS = 5
    active_mining = False
    ledger_sync = True
    no_new_block = False
    ledger = Ledger()
    mem_pool = MemPool()
    peers = []
    semaphore = threading.Semaphore()

    def __init__(self, port):
        self.port = port
        self.address_string = "127.0.0.1:%s" % str(port)
        self.socket_manager = SocketManager(self, port=int(port))
        self.get_peers_from_bootstrap()

    def get_peers_from_bootstrap(self, connection_string=DEFAULT_BOOTSTRAP_NODE, connection_quantity=MAX_CONNECTIONS):
        bootstrap_connection_info = connection_string.split(":")
        MiniCoin.peers = self.socket_manager.send_message(bootstrap_connection_info[0],
                                                          int(bootstrap_connection_info[1]),
                                                          "connect,%s" % str(connection_quantity))

    def start_server(self):
        self.socket_manager.listen()

    def stop_server(self):
        self.socket_manager.stop_server()

    def send_message(self, address_string, command, message=""):
        """
        Helper function to easily format and send messages over sockets.

        Args:
            address_string(str): String representation of the target node in form of "IP:PORT"
            command(str): The message string that identifies the reason for contacting the node.
            message(str): The data to accompany the request being sent.

        Returns:
            str: The response from the target.
        """
        address = address_string.split(":")
        separated_message = str(command) + SocketManager.MESSAGE_SEPARATOR_PATTERN + str(message)
        response = self.socket_manager.send_message(address[0], int(address[1]), separated_message)
        if response == "CONNECTION ERROR":
            if address_string in MiniCoin.peers:
                MiniCoin.peers.remove(address_string)
        if len(MiniCoin.peers) == 0:
            self.get_peers_from_bootstrap()

    def got_message(self, address, message):
        """
        Callback function for when a message is received over sockets.

        Args:
            address: The address of the sender.
            message(str): The message received.

        Returns:
            Some response based on message received.

        Notes:
            Valid messages begin with one of the following strings before the first separator.
                - "new block"
                - "new transaction"
                - "send ledger"

        """
        parsed_message = message.split(SocketManager.MESSAGE_SEPARATOR_PATTERN)
        if parsed_message[0] == "new block":
            self.__got_new_block(Block.block_from_string(parsed_message[2]))
        elif parsed_message[0] == "new transaction":
            self.__got_new_transaction(Transaction.transaction_from_string(parsed_message[2]))
        elif parsed_message[0] == "check ledger":
            return self.check_ledger()
        elif parsed_message[0] == "send ledger":
            return self.send_ledger()
        return "COMPLETE"

    def start_mining(self, block=None):
        """
        Call to start mining for blocks. Kicks off a mining thread.

        Args:
            block(Block): Optional block to begin mining, create a new block if None is provided.

        Returns:
            Block:
                A newly minted block.
        """
        # Shoot off a thread to mine on, thread will repeat until this function ends on user input.
        MiniCoin.no_new_block = True
        MiniCoin.active_mining = True
        threading.Thread(target=self.__threaded_miner, args=[block]).start()
        print("Press ENTER to stop mining at any time!")
        MiniCoin.active_mining = False

    def __threaded_miner(self, block=None):
        """
        Called by thread, mines a block in a new thread.

        Args:
            block(Block): Optional block to begin mining, create a new block if None is provided.

       Returns:
            Block:
                A newly minted block. Returns None if loop is exited without solving the block.
        """
        # Loop until user input.
        while MiniCoin.active_mining:
            # Generate a new block to test random nonce on.
            if block is None:
                mining_block = Block(MiniCoin.ledger.size(), MiniCoin.mem_pool.get_n_tx(Block.TRANSACTIONS_PER_BLOCK),
                                     MiniCoin.ledger.get_last_block().block_hash)
            else:
                mining_block = block
            while MiniCoin.no_new_block and MiniCoin.ledger_sync and mining_block.block_id == MiniCoin.ledger.size() \
                    and MiniCoin.active_mining:
                # While a block has not been found and node considers its ledger up to date, generate a random nonce,
                # has the mining block and if it conforms to the hash pattern return it, otherwise repeat.
                random_nonce = random.random()
                mining_block.nonce = random_nonce
                block_hash = HashFunctions.hash_input(mining_block)
                if block_hash[0:len(self.HASH_PATTERN)] == self.HASH_PATTERN and MiniCoin.no_new_block:
                    mining_block.block_hash = block_hash
                    self.__announce_minted_block(mining_block)
            time.sleep(1)
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
        current_head_block = MiniCoin.ledger.get_last_block()
        # All the following requirements must be met for this block to be a valid head of the current ledger.
        if MiniCoin.ledger.size() >= 1 and block.block_id == current_head_block.block_id + 1 and \
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
        for connection in MiniCoin.peers:
            threading.Thread(target=self.send_message, args=(connection, "new transaction", str(transaction))).start()

    def propagate_block(self, block):
        """
        Forwards a block to all peers.

        Args:
            block(Block): Block to propagate.

        Returns:

        """
        for connection in MiniCoin.peers:
            threading.Thread(target=self.send_message, args=(connection, "new block", str(block))).start()

    def __announce_minted_block(self, block):
        """
        Verifies block minted by node and appends it to ledger if valid.

        Args:
            block(Block): Freshly minted block
        """
        if self.validate_block(block):
            MiniCoin.semaphore.acquire()
            MiniCoin.no_new_block = False
            MiniCoin.ledger.add_block(block)
            MiniCoin.semaphore.release()
            self.propagate_block(block)

    def __got_new_transaction(self, transaction):
        MiniCoin.semaphore.acquire()
        if MiniCoin.mem_pool.add_tx(transaction):
            self.announce_transaction(transaction)
        MiniCoin.semaphore.release()

    def __got_new_block(self, block):
        MiniCoin.semaphore.acquire()
        if self.validate_block(block):
            MiniCoin.ledger.add_block(block)
            self.propagate_block(block)
        MiniCoin.semaphore.release()

    def sync_ledger(self):
        # Make threads for each connection.
        # Connect to the node with longest blockchain and request it if greater than current.
        future_list = []
        executor = ThreadPoolExecutor()
        # Create threads.
        for address in MiniCoin.peers:
            future_list.append([executor.submit(self.send_message, [address, "check ledger"]), address])
        calls_complete = False
        # Block until all calls complete.
        while not calls_complete:
            calls_complete = True
            for future in future_list:
                if future[0].done() is False:
                    calls_complete = False

        # Find node with longest list.
        longest_chain = [0]
        address = None
        for future in future_list:
            result = future[0].result().split(":")
            if int(result[0]) > int(longest_chain[0]):
                longest_chain = result
                address = future[1]
        # Check if longest chain is longer than ours and both share same genesis block.
        if MiniCoin.ledger.size() < int(longest_chain[0]) and \
                longest_chain[2] == MiniCoin.ledger.get_genesis_block().block_hash:
            # Request new blockchain and replace ours with it.
            new_ledger = self.send_message(address, "send ledger")
            MiniCoin.ledger.replace_blockchain(Ledger.ledger_from_string(new_ledger))

    def check_ledger(self):
        MiniCoin.semaphore.acquire()
        genesis_hash = MiniCoin.ledger.get_genesis_block().block_hash
        head_block_hash = MiniCoin.ledger.get_last_block().block_hash
        blockchain_length = str(MiniCoin.ledger.size())
        MiniCoin.semaphore.release()
        return "%s:%s:%s" % (blockchain_length, head_block_hash, genesis_hash)

    def request_ledger(self, target_address_string):
        MiniCoin.semaphore.acquire()
        MiniCoin.ledger_sync = False
        response = self.send_message(target_address_string, "send ledger")
        peer_ledger = Ledger.ledger_from_string(response)
        MiniCoin.ledger.replace_blockchain(peer_ledger)
        MiniCoin.ledger_sync = True
        MiniCoin.semaphore.release()

    def send_ledger(self):
        return str(MiniCoin.ledger)


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
    genesis_tx_hash = HashFunctions.hash_input("genesis")
    genesis_transaction = Transaction(genesis_tx_hash, "genesis")
    genesis = Block(0, [genesis_transaction], "0")
    start_time = datetime.now()
    count = 0
    total_time = 0
    while count < 20:
        rand_num = random.random()
        genesis.nonce = rand_num
        hash_value = HashFunctions.hash_input(genesis)
        if hash_value[:6] == "00ff00":
            print("%s\nHash = %s\nTook %s" % (str(genesis), hash_value, datetime.now() - start_time))
            count += 1
            total_time += int((datetime.now() - start_time).microseconds)
            start_time = datetime.now()
    print("Avg time: %s" % str(total_time / 20))
