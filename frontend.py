import datetime
import json

import requests
from flask import render_template, redirect, request

from app import app

#Node in the blockchain network that our application communicates with
#to fetch and add data
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

posts = []

def fetch_posts():
    '''
    Function to fetch the chain from a blockchain, parse and store locally
    '''

    get_chain_address = '{}/chain'.format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)

        for block in chain['chain']:
            for tx in block['transactions']:
                tx['index'] = block['inedx']
                tx['hash'] = block['previous_hash']
                content.append(tx)

        global posts
        posts = sorted(content,
                       key=lambda k: k['timestamp'],
                       reverse=True)

@app.route('/submit', methods=['POST'])
def submit_text_area():
    '''
    Endpoint to create new transactions via out application
    '''
    post_content = request.form['content']
    author = request.form('author')

    post_object = {
        'author': author,
        'content': post_content
    }
    #Submit transaction_
    new_tx_address = '{}/new_transaction'.format(CONNECTED_NODE_ADDRESS)
    request.post(new_tx_address,
                 json=post_object,
                 headers={'Content-type': 'application/js'})
    return redirect('/')



