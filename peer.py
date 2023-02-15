import random 
from transaction import Transaction
from block import Block
from tree import Node
import graphviz

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
        self.node_block_map = {genesis.blkid: self.root}
        self.hashing_power = config["hashing power"]

    def use_network(self, network):
        self.network = network

    def add_neighbor(self, neighbor):
        self.neighbors.append(neighbor)

    def disconnect_peer(self):
        self.neighbors = []
    
    def generate_transactions(self, Ttx, peers):
        while True:
            r = random.expovariate(1/Ttx)
            coins = random.randint(1, 5)
            yield self.env.timeout(r)

            receiver = random.choice(peers)
            while receiver == self:
                receiver = random.choice(peers)
            # generate a random transaction id by hashing the sender, receiver and time
            id = hash(str(self.id) + str(receiver.id) + str(self.env.now))

            transaction = Transaction(id, self, receiver, coins, self.env.now)
            yield self.env.process(self.forward_transaction(transaction))
    
    def receive_transaction(self, transaction):
        self.transactions.add(transaction)
        yield self.env.process(self.forward_transaction(transaction))

    def forward_transaction(self, transaction):
        # The structure of self.transaction_routing_table is:
        # {recipient_peer: [list of TxIDs either sent to or received from this peer]}
        for n in self.neighbors:
            id = transaction.id
            if n in self.transaction_routing_table.keys():
                # Send this transaction to that neighbor some how
                # print(f"Peer {self.id} is sending transaction {id} to peer {n.id}")
                yield self.env.process(self.network.send_transaction(self, n, transaction))
                if id not in self.transaction_routing_table[n]:
                    self.transaction_routing_table[n].append(id)            
            else:
                # Send this transaction to that neighbor some how
                # print(f"Peer {self.id} is sending transaction {id} to peer {n.id}")
                yield self.env.process(self.network.send_transaction(self, n, transaction))
                self.transaction_routing_table[n] = [id]


    def receive_block(self, block):
        print("receive called")
        isValid = block.validate()
        if not isValid:
            # print("Block is not valid")
            return

        # Add the block to the tree
        node = Node(block, self.env.now)
        parent = self.node_block_map[block.prevblock.blkid]
        parent.children.append(node)

        # Update the node_block_map
        self.node_block_map[block.blkid] = node

        print("Block height", block.height)
        print("Old longest chain height", self.longest_chain.height)

        # Assuming currently that block.height has the correct height
        if block.height > self.longest_chain.height:
            print(f"Peer {self.id} has a new longest chain")
            self.longest_chain = block
            self.balance = block.balances[self.id]

            # New longest chain created
            # Simulating PoW
            yield self.env.process(self.create_block())

        elif block.height == self.longest_chain.height and block.timestamp < self.longest_chain.timestamp:
            print("Peer {self.id} has a new longest chain with same height")
            self.longest_chain = block
            self.balance = block.balances[self.id]

    def create_block(self):
        # while True:
        longest_chain_transactions = self.longest_chain.get_all_transactions()
        valid_transactions = self.transactions - longest_chain_transactions

        num_transactions = random.randint(0, min(len(valid_transactions), 999))
        transactions = random.sample(valid_transactions, num_transactions)
        longest_chain = self.longest_chain
        block = Block(longest_chain, self.env.now, set(transactions), self.id)

        # Haven't checked if the block is valid or not
        # So, some transactions might get lost
        isValid = block.validate()
        if not isValid:
            return

        # Next block timestamp (tk + Tk)
        Tk = random.expovariate(self.hashing_power/self.network.interarrival)

        yield self.env.timeout(Tk)

        new_longest_chain = self.longest_chain
        if new_longest_chain == longest_chain:
            yield self.env.process(self.broadcast_block(block))

            # Modify the longest chain and add the block to the tree
            self.longest_chain = block
            node = Node(block, self.env.now)
            parent = self.node_block_map[block.prevblock.blkid]
            parent.children.append(node)

            self.node_block_map[block.blkid] = node


    def broadcast_block(self, block):
        # The structure of self.block_routing_table is:
        # {recipient_peer: [list of blockIDs either sent to or received from this peer]}

        for n in self.neighbors:
            id = block.blkid
            if n in self.block_routing_table.keys():
                # Send this block to that neighbor some how
                yield self.env.process(self.network.send_block(self, n, block))
                # print("Block sent")
                if id not in self.block_routing_table[n]:
                    self.block_routing_table[n].append(id)            
            else:
                # Send this block to that neighbor some how
                yield self.env.process(self.network.send_block(self, n, block))
                # print("Block sent")
                self.block_routing_table[n] = [id]

    def print_tree(self, filename):
        f = graphviz.Digraph(filename)

        reverse_mapping = {}

        for id, blkid in enumerate(self.node_block_map.keys()):
            reverse_mapping[blkid] = id
            f.node(str(id), str(blkid) + " : " + str(self.node_block_map[blkid].timestamp))

        # Do BFS and add edges
        queue = [self.root]
        while queue:
            node = queue.pop(0)
            for child in node.children:
                f.edge(str(reverse_mapping[node.block.blkid]), str(reverse_mapping[child.block.blkid]))
                queue.append(child)

        f.render()