from hashlib import sha256
import json
import time


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        '''
        Constructor for the 'Block' class
        :param idx: Unique ID of the block
        :param transactions: List of transactions
        :param timestamp: Time of block generation
        :param previous_hash: A hash of the block before this block, for chaining the blocks
        '''

        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash

    def compute_hash(self):
        '''
        Retunrs the hash of the block by first converting it to a JSON string
        '''
        block_string = json.dump(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    difficulty = 2 #difficulty of Porrf of work algorithm
    def __init__(self):
        '''
        Constructor for the 'Blockchain' class
        '''

        self.chain = []
        self.create_genesis_block() #The first block with no previous block is known as genesis block
        self.unconfirmed_transactions = []

    def create_genesis_block(self):
        '''
        A function to create the genesis block and appends it to the chain. The
        block has a previous hash  of 0, an index 0 and a valid hash
        '''

        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        '''
        :return: the last block in the chain; the chain always contains at least a block
        '''
        return self.chain[-1]

    def proof_of_work(self, block):
        '''
        A function that tries different values of the nonce to get a hash that satisfies our
        difficulity criteria
        '''

        block.nonce = 0
        computed_hash = block.compute_hash()

        while not computed_hash.startswith('0'*Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_block(self, block, proof):
        '''
        A function that adds blocks to the chain after verification
        '''

        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def is_valid_proof(self, block, block_hash):
        return block_hash.startswith('0' * Blockchain.difficulty) and block_hash == block.compute_hash

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def mine(self):
        '''
        A function that serves as an interface to add pending transactions to the blockchain by adding
        them to the block and figuring out proof of work
        '''

        if not self.unconfirmed_transactions:
            return False
        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
        return new_block.index

    def check_chain_validity(cls, chain):
        '''
        A helper method to check if the entire blockchain is valid.
        '''

        result = True
        previous_hash = '0'

        for block in chain:
            block_hash = block.hash
            #Remove the hash attribute and recompute the hash
            delattr(block, 'hash')

            if not cls.is_valid_proof(block, block_hash) or previous_hash != block.previous_hash:
                result = False
                break
            block.hash, previous_hash = block_hash, block_hash
        return result

