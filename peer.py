import random 
from transaction import Transaction
from block import Block
from tree import Node
import graphviz
import os

class Peer:
    """
    A peer(node) in the network
    """
    def __init__(self, id, genesis, env, config) -> None:      
        """
        id: unique id of the peer
        genesis: genesis block
        env: simpy environment
        config: dictionary containing the configuration of the peer
        """
        self.id = id
        self.neighbors = []
        self.genesis = genesis
        self.speed = config["speed"] # slow or fast 
        self.cpu = config["cpu"]   # low or high
        self.balance = 0 
        self.longest_chain = genesis
        self.transactions = set([])
        self.num_gen = 0

        self.transaction_routing_table = {}
        self.block_routing_table = {}

        self.env = env
        self.network = None
        self.root = Node(genesis, self.env.now)
        self.node_block_map = {genesis.blkid: self.root}
        self.hashing_power = config["hashing power"]

    def use_network(self, network):
        """
        Use the network to send transactions and blocks

        network: network to be used
        """
        self.network = network

    def add_neighbor(self, neighbor):
        """
        Add a neighbor to the peer
        """
        self.neighbors.append(neighbor)

    def disconnect_peer(self):
        """
        Disconnect the peer from the network
        """
        self.neighbors = []
    
    def generate_transactions(self, Ttx, peers):
        """
        Generate transactions at a rate of Ttx

        Ttx: mean interarrival time of transactions
        peers: list of all peers in the network

        returns: a generator
        """
        while True:
            r = random.expovariate(1/Ttx) # same as exponential distribution with mean Ttx
            coins = random.randint(1, 5)
            yield self.env.timeout(r)

            receiver = random.choice(peers)
            while receiver == self:
                receiver = random.choice(peers)
            # generate a random transaction id by hashing the sender, receiver and time
            id = hash(str(self.id) + str(receiver.id) + str(self.env.now))

            transaction = Transaction(id, self, receiver, coins, self.env.now)
            yield self.env.process(self.forward_transaction(transaction))

            print(f"Peer {self.id} generated transaction {id} at time {self.env.now}")
    
    def receive_transaction(self, sender, transaction):
        """
        Receive a transaction from a sender
        """
        self.transactions.add(transaction) # add the transaction to the set of transactions 
        # change routing table to not send transaction back to sender
        if sender in self.transaction_routing_table.keys():
            if transaction.id not in self.transaction_routing_table[sender]:
                self.transaction_routing_table[sender].append(transaction.id)
        else:
            self.transaction_routing_table[sender] = [transaction.id]
        yield self.env.process(self.forward_transaction(transaction))

    def forward_transaction(self, transaction):
        """
        Forward a transaction to all neighbors

        transaction: transaction to be forwarded
        """
        # Forward a transaction to all neighbors
        # The structure of self.transaction_routing_table is:
        # {recipient_peer: [list of TxIDs either sent to or received from this peer]}
        for n in self.neighbors:
            id = transaction.id
            if n in self.transaction_routing_table.keys():
                # Send this transaction to the neighbor if it has not been sent to it before (to avoid loops)
                # print(f"Peer {self.id} is sending transaction {id} to peer {n.id}")
                if id not in self.transaction_routing_table[n]:
                    self.transaction_routing_table[n].append(id)
                    yield self.env.process(self.network.send_transaction(self, n, transaction))
            else:
                # Send this transaction to that neighbor 
                # print(f"Peer {self.id} is sending transaction {id} to peer {n.id}")
                self.transaction_routing_table[n] = [id]
                yield self.env.process(self.network.send_transaction(self, n, transaction))


    def receive_block(self, sender, block):
        """
        Receive a block from a peer and add it to the tree if it is valid and update the longest chain

        block: block to be received
        """
        # Receive a block from a peer
        #print("receive called")
        isValid = block.validate()
        if not isValid:
            # print("Block is not valid")
            return

        print("Peer ID : ", self.id)
        print("Block was generated by : ", block.userid)
        print("Current block ID : ", block.blkid)
        print("Previous block ID : ", block.prevblock.blkid)
        to_create = False

        if block.prevblock.blkid in self.node_block_map.keys():
            # Add the block to the tree
            parent = self.node_block_map[block.prevblock.blkid]
            node = Node(block, self.env.now)
            print(f"{self.id} : Searching for {node.block.blkid} in {parent.children}")
            if node.block.blkid not in parent.children:
                print("Adding the node to the tree")
                print("Edge from ", parent.block.blkid, " to ", node.block.blkid)
                parent.children.append(node.block.blkid)
                self.node_block_map[block.prevblock.blkid] = parent
                print("New children array : ", self.node_block_map[block.prevblock.blkid].children)
                pass

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
                to_create = True

            elif block.height == self.longest_chain.height and block.timestamp < self.longest_chain.timestamp:
                print(f"Peer {self.id} has a new longest chain with same height")
                self.longest_chain = block
                self.balance = block.balances[self.id]

                # New longest chain created
                # Simulating PoW
                to_create = True

        # Update routing table to not send block back to sender
        if sender in self.block_routing_table.keys():
            if block.blkid not in self.block_routing_table[sender]:
                self.block_routing_table[sender].append(block.blkid)
        else:
            self.block_routing_table[sender] = [block.blkid]
        yield self.env.process(self.broadcast_block(block))
        if to_create:
            yield self.env.process(self.create_block())
            pass
        

    def create_block(self):
        """
        Create a block and broadcast it to all neighbors in the network 
        """
        # Create a block
        # while True:
        print("Creating a block")
        self.num_gen += 1
        # yield self.env.timeout(self.id*1000)
        longest_chain_transactions = self.longest_chain.get_all_transactions()
        valid_transactions = self.transactions - longest_chain_transactions
        # print(self.transactions, longest_chain_transactions, valid_transactions)
        num_transactions = random.randint(0, min(len(valid_transactions), 999))
        transactions = random.sample(valid_transactions, num_transactions)
        longest_chain = self.longest_chain
        block = Block(longest_chain, self.env.now, set(transactions), self.id)

        # Haven't checked if the block is valid or not
        # So, some transactions might get lost
        isValid = block.validate()
        if not isValid:
            print("Invalid block created")
            return

        # Next block timestamp (tk + Tk)
        Tk = random.expovariate(self.hashing_power/self.network.interarrival)

        yield self.env.timeout(Tk)
        
        new_longest_chain = self.longest_chain
        if new_longest_chain.blkid == longest_chain.blkid:
            print("Chain is same")
            print("Peer ID : ", self.id)
            print("Creating block with block ID : ", block.blkid)
            print("Previous block ID : ", block.prevblock.userid)
            # Modify the longest chain and add the block to the tree
            self.longest_chain = block
            node = Node(block, self.env.now)
            parent = self.node_block_map[block.prevblock.blkid]
            print(f"{self.id} : Searching for {node.block.blkid} in {parent.children}")
            if node.block.blkid not in parent.children:
                print("Adding the node to the tree")
                print("Edge from ", parent.block.blkid, " to ", node.block.blkid)
                parent.children.append(node.block.blkid)
                self.node_block_map[block.prevblock.blkid] = parent
                print("New children array : ", self.node_block_map[block.prevblock.blkid].children)
                pass

            self.node_block_map[block.blkid] = node
            yield self.env.process(self.broadcast_block(block))
            # else:
                # yield self.env.process(self.create_block())
            # self.print_tree(f"debug_plots/tree_{self.id}.dot")


    def broadcast_block(self, block):
        """
        Broadcast the block to all the neighbors in the network and update the block_routing_table
        The structure of self.block_routing_table is:
        {recipient_peer: [list of blockIDs either sent to or received from this peer]}
        """

        # Same as sending transaction
        for n in self.neighbors:
            id = block.blkid
            if n in self.block_routing_table.keys():
                # Send this block to that neighbor some how
                if id not in self.block_routing_table[n]:
                    print(f"{self.id} Broadcasting block to {n.id}")
                    self.block_routing_table[n].append(id)

                    yield self.env.process(self.network.send_block(self, n, block))
            else:
                # Send this block to that neighbor some how
                print(f"{self.id} Broadcasting block to {n.id}")
                self.block_routing_table[n] = [id]

                yield self.env.process(self.network.send_block(self, n, block))
                # print("Block sent")
            print("Block sent")

    def print_tree(self, filename):
        """
        Print the tree in a file using graphviz
        """
        f = graphviz.Digraph(filename, format='png')

        reverse_mapping = {}

        for id, blkid in enumerate(self.node_block_map.keys()):
            reverse_mapping[blkid] = id
            #f.node(str(id), str(blkid) + " : " + str(self.node_block_map[blkid].timestamp))
            if self.node_block_map[blkid].block.prevblock is not None:
                data = str(blkid) + " : " + str(self.node_block_map[blkid].block.userid) + " : " + str(self.node_block_map[blkid].block.prevblock.blkid) + "\n"
                for tx in self.node_block_map[blkid].block.transactions:
                    data += str(tx) + "\n"

                f.node(str(id), data)
            else:
                f.node(str(id), str(blkid) + " : " + str(self.node_block_map[blkid].block.userid))

        for k, v in self.node_block_map.items():
            if(v.block.prevblock is not None):
                print(k, v.block.blkid, v.block.prevblock.blkid)
            else:
                print(k, v.block.blkid)
            print(v.children)

        print()
        print()
        print("Peer ID : ", self.id)

        visited = set()
        edges = set()
        def dfs(visited, nodeBlkid):
            if nodeBlkid not in visited:
                visited.add(nodeBlkid)
                print()
                print("Node : ", nodeBlkid)
                print("Children : ", self.node_block_map[nodeBlkid].children)
                for childID in self.node_block_map[nodeBlkid].children:
                    f.edge(str(reverse_mapping[nodeBlkid]), str(reverse_mapping[childID]))
                    print(f"{nodeBlkid} -> {childID}")
                    dfs(visited, childID)
                print()

        dfs(visited, self.root.block.blkid)

        print()
        print()

        for e in edges:
            f.edge(e[0], e[1])
        f.render()

    def save_tree(self, filename):
        """
        Save the tree in a file using pickle
        """
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        num_longest = 0

        curr_block = self.longest_chain
        prev_block = curr_block.prevblock

        while prev_block is not None:
            if curr_block.userid == self.id:
                num_longest += 1
                
            curr_block = prev_block
            prev_block = curr_block.prevblock

        with open(filename, 'w') as f:

            print("Peer ID : ", self.id, file=f)
            print("Number of blocks created : ", self.num_gen, file=f)
            print("Number of blocks ending in longest chain : ", num_longest, file=f)
            print("Ratio : ", num_longest/self.num_gen, file=f)

            reverse_mapping = {}
            for id, blkid in enumerate(self.node_block_map.keys()):
                reverse_mapping[blkid] = id

            visited = set()
            def dfs(visited, nodeBlkid):
                if nodeBlkid not in visited:
                    visited.add(nodeBlkid)
                    print(file=f)
                    print("Block Hash : ", self.node_block_map[nodeBlkid].block.blkid, file=f)
                    if(self.node_block_map[nodeBlkid].block.prevblock is not None):
                        print("Parent Hash : ", self.node_block_map[nodeBlkid].block.prevblock.blkid, file=f)
                    print("Received at : ", self.node_block_map[nodeBlkid].timestamp, file=f)
                    print(file=f)

                    for childID in self.node_block_map[nodeBlkid].children:
                        dfs(visited, childID)

            dfs(visited, self.root.block.blkid)