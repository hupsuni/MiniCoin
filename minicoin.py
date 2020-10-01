"""
TO RUN:
1. Start Bootstrap Node: python3 minicoin.py --type bootstrap
2. Start 1 or more Nodes or Miners:
    Standalone Node: python3 minicoin.py --type node --port 5001
    Mining Node (NO UI): python3 minicoin.py --type node --port 5002 --mine
3. Start a Node with a UI (Incomplete)
    Node with UI: python3 minicoin.py --type node-ui --port 5003
4. Optional if not running UI.
    Start a node that will sync with the network, wait 10 seconds, print its data, wait 5 seconds and then
    request all its peers also print their data locally.
    - python3 minicoin.py --type node --port 5010 --print
"""
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
from bootstrap import BootStrap
from genesis_block import GenesisBlock


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
        """
        Builds a transaction from its string representation.
        """
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
        self.block_chain.append(Block(GenesisBlock.block_id,
                                      [Transaction(GenesisBlock.genesis_transaction_id,
                                                   GenesisBlock.genesis_transaction_string)],
                                      GenesisBlock.previous_block_hash, GenesisBlock.nonce))

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
        """
        Builds a ledger from its string representation.
        """
        if type(ledger_string) == list:
            ledger_string = ledger_string[0]
        ledger_list = []
        ledger_array = ledger_string.split("BLOCK:")
        if ledger_array[0] == "LEDGER:" and ledger_array[-1] == "LEDGER:":
            for block in ledger_array[1:-1]:
                ledger_list.append(Block.block_from_string(block))
        return ledger_list.copy()

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

    def to_string(self):
        """
        Converts a block to a human readable string.

        Returns:
            str: Human readable string representing a block.

        """
        block_id = "GENESIS BLOCK" if self.block_id == 0 else str(self.block_id)
        return_string = "Block ID: %s\nNonce: %s\nPrevious Blocks Hash: %s\n" % (block_id, str(self.nonce),
                                                                               str(self.previous_block_hash))
        for transaction in self.tx:
            return_string += "Transaction: %s\n" % str(transaction)
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
    REFRESH_RATE = 45
    shutdown = False
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

    def get_peers_from_bootstrap(self, connection_string=DEFAULT_BOOTSTRAP_NODE, connection_quantity=MAX_CONNECTIONS):
        """
        Queries the bootstrap node for a list of active peers.
        """
        print("\nQuerying bootstrap for peers...\n")
        peers = self.send_message(connection_string, "connect", str(connection_quantity))
        if peers[0] == "nodes" and type(peers) == list and len(peers) > 1:
            for address in peers[1:]:
                MiniCoin.semaphore.acquire()
                if address != self.address_string and address not in MiniCoin.peers:
                    MiniCoin.peers.append(address)
                MiniCoin.semaphore.release()

    def start_server(self):
        """
        Starts the socket server for node connections and begins the background threads for blockchain maintenance.
        """
        time.sleep(1)
        self.get_peers_from_bootstrap()
        self.socket_manager.listen()
        self.sync_ledger()
        MiniCoin.shutdown = False
        threading.Thread(target=self.__threaded_sync_ledger).start()

    def __threaded_sync_ledger(self):
        """
        Helper function for looping a thread which will ensure the ledger remains in sync with other nodes.
        """
        while not MiniCoin.shutdown:
            time.sleep(MiniCoin.REFRESH_RATE)
            self.sync_ledger()

    def stop_server(self):
        MiniCoin.shutdown = True
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
        separated_message = str(command) + SocketManager.MESSAGE_SEPARATOR_PATTERN + str(self.port) + \
                            SocketManager.MESSAGE_SEPARATOR_PATTERN + str(message)
        response = self.socket_manager.send_message(address[0], int(address[1]), separated_message)
        if response == "CONNECTION ERROR":
            MiniCoin.semaphore.acquire()
            if "%s:%s" % (address[0], str(address[1])) in MiniCoin.peers:
                MiniCoin.peers.remove("%s:%s" % (address[0], str(address[1])))
            MiniCoin.semaphore.release()
        if len(MiniCoin.peers) == 0 and command != "connect":
            self.get_peers_from_bootstrap()
        return response.split(SocketManager.MESSAGE_SEPARATOR_PATTERN)

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
                - "check ledger"
                - "pretty print"
                - "alive?"
        """
        parsed_message = message.split(SocketManager.MESSAGE_SEPARATOR_PATTERN)
        if "127.0.0.1:%s" % parsed_message[1] not in MiniCoin.peers and len(MiniCoin.peers) < MiniCoin.MAX_CONNECTIONS \
                and "127.0.0.1:%s" % parsed_message[1] != self.address_string and parsed_message[0] != "alive?":
            MiniCoin.semaphore.acquire()
            MiniCoin.peers.append("127.0.0.1:%s" % parsed_message[1])
            MiniCoin.semaphore.release()
        if parsed_message[0] == "new block":
            self.__got_new_block(Block.block_from_string(parsed_message[2]))
        elif parsed_message[0] == "new transaction":
            self.__got_new_transaction(Transaction.transaction_from_string(parsed_message[2]))
        elif parsed_message[0] == "check ledger":
            return self.check_ledger()
        elif parsed_message[0] == "send ledger":
            return self.send_ledger()
        elif parsed_message[0] == "pretty print":
            self.pretty_print()
        elif parsed_message[0] == "alive?":
            return True
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
        time.sleep(.1)
        threading.Thread(target=self.__threaded_miner, args=[block]).start()
        print("Press ENTER to stop mining at any time!")
        input()
        MiniCoin.active_mining = False
        print("Miner stopping.")

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
            random.seed()
            print("Mining blocks in new thread...")
            # Generate a new block to test random nonce on.
            if block is None:
                MiniCoin.semaphore.acquire()
                mining_block = Block(MiniCoin.ledger.size(), MiniCoin.mem_pool.get_n_tx(Block.TRANSACTIONS_PER_BLOCK),
                                     MiniCoin.ledger.get_last_block().block_hash)
                MiniCoin.semaphore.release()
            else:
                mining_block = block
            MiniCoin.semaphore.acquire()
            while MiniCoin.no_new_block and MiniCoin.ledger_sync and mining_block.block_id == MiniCoin.ledger.size() \
                    and MiniCoin.active_mining:
                MiniCoin.semaphore.release()
                # While a block has not been found and node considers its ledger up to date, generate a random nonce,
                # has the mining block and if it conforms to the hash pattern return it, otherwise repeat.
                random_nonce = random.random()
                mining_block.nonce = random_nonce
                block_hash = HashFunctions.hash_input(mining_block)
                MiniCoin.semaphore.acquire()
                if block_hash[0:len(self.HASH_PATTERN)] == self.HASH_PATTERN and MiniCoin.no_new_block:
                    MiniCoin.semaphore.release()
                    mining_block.block_hash = block_hash
                    print("\nNew block discovered:\n%s" % str(mining_block))
                    self.__announce_minted_block(mining_block)
                    MiniCoin.semaphore.acquire()
            MiniCoin.semaphore.release()
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
        print("\nValidating new block:\n%s" % str(block))
        MiniCoin.semaphore.acquire()
        hash_to_validate = block.block_hash
        current_head_block = MiniCoin.ledger.get_last_block()
        # All the following requirements must be met for this block to be a valid head of the current ledger.
        if MiniCoin.ledger.size() >= 1 and block.block_id == current_head_block.block_id + 1 and \
                block.previous_block_hash == current_head_block.block_hash and \
                HashFunctions.hash_input(block) == block.block_hash and \
                hash_to_validate[0:len(self.HASH_PATTERN)] == self.HASH_PATTERN:
            MiniCoin.semaphore.release()
            print("\nNew Block is Acceptable\n")
            return True
        MiniCoin.semaphore.release()
        print("\nNew Block Invalid\n")
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
            print("\nPropagating block: %s to peer: %s\n" % (str(block.block_id), connection))
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
            time.sleep(1)
            MiniCoin.no_new_block = True
            MiniCoin.semaphore.release()
            self.propagate_block(block)

    def __got_new_transaction(self, transaction):
        """
        A new transaction has been received.
        """
        MiniCoin.semaphore.acquire()
        is_new = MiniCoin.mem_pool.add_tx(transaction)
        MiniCoin.semaphore.release()
        if is_new:
            self.announce_transaction(transaction)

    def __got_new_block(self, block):
        """
        A new block has been received, ensure it is valid and not already present in the nodes current chain.
        If it is both new and valid, append it and announce its existence to all peers, otherwise ignore.

        Args:
            block(Block): New block.
        """
        is_new = self.validate_block(block)
        if is_new:
            print("\nNew block received:\n%s" % str(block))
            MiniCoin.semaphore.acquire()
            MiniCoin.ledger.add_block(block)
            MiniCoin.semaphore.release()
            self.propagate_block(block)

    def sync_ledger(self):
        """
        Designed to be run in background and called infrequently, this function contacts all this nodes peers.
        It requests some basic information about their ledger. If One or more nodes has a longer ledger than this
        node it will request a copy of that ledger and, should the genesis block be the same as this nodes genesis block
        it will update its ledger accordingly.
        """
        print("\nChecking ledger is up to date...\n")
        future_list = []
        executor = ThreadPoolExecutor()
        # Create threads.
        for address in MiniCoin.peers:
            future_list.append([executor.submit(self.send_message, address, "check ledger"), address])
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
        MiniCoin.semaphore.acquire()
        for future in future_list:
            return_value = future[0].result()[0]
            if return_value is not None and return_value != "":
                result = return_value.split(":")
                if result[0] != "CONNECTION ERROR" and int(result[0]) > int(longest_chain[0]):
                    longest_chain = result
                    address = future[1]
        current_size = MiniCoin.ledger.size()
        genesis_hash = MiniCoin.ledger.get_genesis_block().block_hash
        MiniCoin.semaphore.release()
        # Check if longest chain is longer than ours and both share same genesis block.
        if current_size < int(longest_chain[0]) and longest_chain[2] == genesis_hash:
            print("\nLedger is out of sync, requesting update from peer: %s\n" % address)
            # Request new blockchain and replace ours with it.
            new_ledger = self.send_message(address, "send ledger")
            MiniCoin.semaphore.acquire()
            MiniCoin.ledger_sync = False
            MiniCoin.ledger.replace_blockchain(Ledger.ledger_from_string(new_ledger))
            print("New ledger accepted")
            MiniCoin.semaphore.release()
            time.sleep(1)
            MiniCoin.semaphore.acquire()
            MiniCoin.ledger_sync = True
            MiniCoin.semaphore.release()
        else:
            print("\nLedger is up to date!\n")

    def check_ledger(self):
        """
        Fields a request from a peer, responding with some information about the state of this nodes ledger.

        Returns:
            str: A string detailing the current ledger information in the form of:
                current length, the hash of the head block, the hash of the genesis block.
                Separated by colons.
        """
        MiniCoin.semaphore.acquire()
        genesis_hash = MiniCoin.ledger.get_genesis_block().block_hash
        head_block_hash = MiniCoin.ledger.get_last_block().block_hash
        blockchain_length = str(MiniCoin.ledger.size())
        MiniCoin.semaphore.release()
        return "%s:%s:%s" % (blockchain_length, head_block_hash, genesis_hash)

    def request_ledger(self, target_address_string):
        """
        Requests a copy of the ledger from a specific peer.

        Args:
            target_address_string(str): The address of the peer to send the request to.

        """
        MiniCoin.ledger_sync = False
        response = self.send_message(target_address_string, "send ledger")
        peer_ledger = Ledger.ledger_from_string(response)
        MiniCoin.semaphore.acquire()
        MiniCoin.ledger.replace_blockchain(peer_ledger)
        MiniCoin.ledger_sync = True
        MiniCoin.semaphore.release()

    def send_ledger(self):
        """
        Returns a copy of this nodes ledger as a string.
        """
        print("\nA peer has requested a copy of our ledger, sending...\n")
        return str(MiniCoin.ledger)

    def pretty_print(self):
        """
        Simple function to print the information about this node in a human readable form.
        """
        MiniCoin.semaphore.acquire()
        print("Node address: %s\n"
              "***Connected Nodes***\n" % self.address_string)
        for address in MiniCoin.peers:
            print("%s\n" % address)
        print("*****Blockchain*****\n")
        for block in MiniCoin.ledger.block_chain:
            print("%s" % block.to_string())
        print("\n***Mem Pool***\n")
        for tx in MiniCoin.mem_pool.tx:
            print("Transaction: %s\n" % str(tx))
        MiniCoin.semaphore.release()

    def request_peers_print(self):
        """
        Sends a request to all peers asking them to print their details locally.
        """
        MiniCoin.semaphore.acquire()
        for address in MiniCoin.peers:
            self.send_message(address, "pretty print")
            time.sleep(1)
        MiniCoin.semaphore.release()


class ClientInterface(MiniCoin):  # TODO - Complete interface for ease of use for demo.
    def __init__(self, port):
        super().__init__(port)
        self.start_server()

    def client_interface(self):
        pass


if __name__ == '__main__':
    # Parse CLI arguments
    argv = sys.argv[1:]
    options, arguments = getopt.getopt(argv, "", ["port=", "type=", "mine", "print"])
    option_dict = {
        "--port": None,
        "--type": None,
        "--mine": None,
        "--print": None
    }
    for option in options:
        option_dict[option[0]] = option[1]
    node = None
    try:
        if option_dict["--type"] == "bootstrap":
            print("Starting bootstrap server")
            node = BootStrap()
            node.run()
        elif option_dict["--type"] == "node" and option_dict["--port"] is not None:
            print("Starting node")
            node = MiniCoin(int(option_dict["--port"]))
            node.start_server()
            if option_dict["--mine"] is not None:
                node.start_mining()
            elif option_dict["--print"] is not None:
                while True:
                    time.sleep(10)
                    node.pretty_print()
                    time.sleep(5)
                    node.request_peers_print()
        elif option_dict["--type"] == "node-ui" and option_dict["--port"] is not None:
            node = ClientInterface(int(option_dict["--port"]))
            node.start_server()
            node.client_interface()
        else:
            print("Please specify a --type as \"bootstrap\", \"node\" or \"client\"!\n"
                  "If not starting a bootstrap node you must also specify a port number to listen on.")
    except KeyboardInterrupt:
        node.stop_server()
