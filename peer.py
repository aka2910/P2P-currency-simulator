import random 
from transaction import Transaction
from block import Block
import time
from tree import Node
import graphviz

# I is the average interarrival time between blocks
I = 600

class Peer:
    def __init__(self, id, genesis, env, config) -> None:
        self.id = id
        self.neighbors = []
        self.genesis = genesis
        self.speed = config["speed"] # slow or fast 
        self.cpu = config["cpu"]   # low or high
        self.balance = 0    
        self.longest_chain = genesis
        self.transactions = set([])

        self.transaction_routing_table = {}
        self.block_routing_table = {}

        self.env = env
        self.network = None
        self.root = Node(genesis, self.env.now)
        self.node_block_map = {genesis: self.root}

    def use_network(self, network):
        self.network = network

    def add_neighbor(self, neighbor):
        self.neighbors.append(neighbor)

    def disconnect_peer(self):
        self.neighbors = []
    
    def generate_transactions(self, Ttx, time, peers):
        while True:
            r = random.expovariate(1/Ttx)
            coins = random.randint(1, 100)
            yield self.env.timeout(r)

            receiver = random.choice(peers)
            while receiver == self:
                receiver = random.choice(peers)
            # generate a random transaction id by hashing the sender, receiver and time
            id = hash(str(self.id) + str(receiver.id) + str(self.env.now))

            transaction = Transaction(id, self, receiver, coins, self.env.now)
            self.forward_transaction(transaction)
    
    def receive_transaction(self, transaction):
        self.transactions.add(transaction)
        self.forward_transaction(transaction)

    def forward_transaction(self, transaction):
        # The structure of self.transaction_routing_table is:
        # {recipient_peer: [list of TxIDs either sent to or received from this peer]}

        for n in self.neighbors:
            id = transaction.id
            if n in self.transaction_routing_table.keys():
                # Send this transaction to that neighbor some how
                self.network.send_transaction(self, n, transaction)
                if id not in self.transaction_routing_table[n]:
                    self.transaction_routing_table[n].append(id)            
            else:
                # Send this transaction to that neighbor some how
                self.network.send_transaction(self, n, transaction)
                self.transaction_routing_table[n] = [id]


    def receive_block(self, block):
        isValid = block.validate()
        if not isValid:
            return

        # Add the block to the tree
        node = Node(block, self.env.now)
        parent = self.node_block_map[block.prevblock]
        parent.children.append(node)

        # Update the node_block_map
        self.node_block_map[block] = node

        # Assuming currently that block.height has the correct height
        if block.height > self.longest_chain.height:
            self.longest_chain = block
            self.balance = block.balances[self.id]

            # New longest chain created
            # Simulating PoW
            self.env.process(self.create_block())

        elif block.height == self.longest_chain.height and block.timestamp < self.longest_chain.timestamp:
            self.longest_chain = block
            self.balance = block.balances[self.id]

    def create_block(self):
        while True:
            longest_chain_transactions = self.longest_chain.get_all_transactions()
            valid_transactions = self.transactions - longest_chain_transactions

            num_transactions = random.randint(0, min(len(valid_transactions), 999))
            transactions = random.sample(valid_transactions, num_transactions)
            longest_chain = self.longest_chain
            block = Block(longest_chain, self.env.now, set(transactions), self.id)

            # Haven't checked if the block is valid or not
            # So, some transactions might get lost

            # Next block timestamp (tk + Tk)
            Tk = random.expovariate(self.hashing_power/I)

            yield self.env.timeout(Tk)

            new_longest_chain = self.longest_chain
            if new_longest_chain == longest_chain:
                self.broadcast_block(block)

                # Remove these transactions from the pool
                self.transactions = self.transactions - set(transactions)


    def broadcast_block(self, block):
        # The structure of self.block_routing_table is:
        # {recipient_peer: [list of blockIDs either sent to or received from this peer]}

        for n in self.neighbors:
            id = block.blkid
            if n in self.block_routing_table.keys():
                # Send this block to that neighbor some how
                self.network.send_block(self, n, block)
                if id not in self.block_routing_table[n]:
                    self.block_routing_table[n].append(id)            
            else:
                # Send this block to that neighbor some how
                self.network.send_block(self, n, block)
                self.block_routing_table[n] = [id]

    def print_tree(self, filename):
        f = graphviz.Digraph(filename)

        for id, block in enumerate(self.node_block_map.keys()):
            f.node(str(id), str(block.blkid) + " : " + str(self.node_block_map[block].timestamp))

        # Do BFS and add edges
        queue = [self.root]
        while queue:
            node = queue.pop(0)
            for child in node.children:
                f.edge(str(id), str(child.block.blkid))
                queue.append(child)

        f.render()