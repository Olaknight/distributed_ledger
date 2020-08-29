from blockchain.block import Blockchain, Block
from flask import Flask, request
import requests
import time
import json
app = Flask(__name__)

#Initialize the blockchain object
blockchain = Blockchain()

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["author", "content"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404
    tx_data["timestamp"] = time.time()
    blockchain.add_new_transaction(tx_data)

    return "Success", 201


@app.route('/mine', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block)
    return json.dumps({
        "length": len(chain_data),
        "chain": chain_data })


@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    return "Block #{} is mined".format(result)


@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)

#Contains the host addresses of the other participating members of the network
peers = set()

#Endpoint to add new peers to the network
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    #The host address to the peer node
    node_address = request.get_json()['node_address']
    if   not node_address:
        return "Invalid data", 400

    #Adding new node to the pool of nodes in the network
    peers.add(node_address)

    #Return the blockchain to the newly registered node, for blockchain consistency
    return get_chain()

@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    '''
    Internally calls the register_node endpoint to
    register current_node with the remote node specified in the request,
    and sync the blockchain as well with the remote node.
    '''

    node_address = request.get_json(['node_address'])

    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    #Make a request to register with remote node and ov=btain info
    response = requests.post(node_address + '/register_node', data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peeers
        #Update  chain and peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
    else:
        return response.content, response.status_code

def create_chain_from_dump(chain_dump):
    blockchain = Blockchain()

    for idx, block_data in enumerate(chain_dump):
        block = Block( block_data['index'],
                       block_data['transaction'],
                       block_data['timestamp'],
                       block_data['previous_hash'])

        proof = block_data['hash']
        if idx > 0:
            added = blockchain.add_block(block, proof)
            if not added:
                raise Exception('The chain dump has been added')
        else:
            blockchain.chain.append(block) #Genesis block needs no verification
    return blockchain


def consensus():
    '''
    Algorithm to simply check if the longer chain is valid, then,
    our chain is replaced by it
    '''
    global blockchain

    current_len = len(blockchain)
    longest_chain = None

    for node in peers:
        response = requests.get('{}/chain'.format(node))
        length = request.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True
    return False

@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data['index'],
                  block_data['transaction'],
                  block_data['timestamp'],
                  block_data['previous_hash'])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400
    return 'Block has been added to the chain', 201

def announce_new_block(block):
    '''
    A function to update  the chain of other nodes in the network,
    once a block has been mined
    '''

    for peer in peers:
        url = '{}/add_block'.format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))

@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return 'No transaction to mine'
    else:
        chain_length = len(blockchain.chain)
        consensus()
        if chain_length == len(blockchain.chain):
            announce_new_block(blockchain.last_block)
        return "Block #{} is mined.".format(blockchain.last_block.index)







