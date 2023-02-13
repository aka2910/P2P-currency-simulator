import random 
from transaction import Transaction
from block import Block
import time
from run import Simulator

# I is the average interarrival time between blocks
I = 600

sim = Simulator()

class Peer:
    def __init__(self, id, genesis) -> None:
        self.id = id
        self.neighbors = []
        self.genesis = genesis
        self.speed = "" # slow or fast 
        self.cpu = ""   # low or high
        self.balance = 0    
        self.longest_chain = genesis
        self.transactions = set([])

        self.routing_table = {}
    
    def add_neighbor(self, neighbor):
        self.neighbors.append(neighbor)

    def disconnect_peer(self):
        self.neighbors = []
    
    def generate_transactions(self, Ttx, time, peers):
        # generate transaction for block
        # send transaction to neighbors
        # Each peer generates transactions randomly in time. The interarrival between transactions generated by
        # time is between 0 to time. generate transactions 
        # any peer is chosen from an exponential distribution whose mean time(Ttx) can be set as a parameter of the
        transactions = []
        times = []
        start_time = 0
        while start_time < time:
            t = random.expovariate(1/Ttx)
            start_time += t
            times.append(start_time)
        for t in times:
            # choose a random peer
            receiver = random.choice(peers)
            while receiver == self:
                receiver = random.choice(peers)
            # generate a random transaction id by hashing the sender, receiver and time
            id = hash(str(self.id) + str(receiver.id) + str(t))
            
            transactions.append(Transaction(id, self, receiver, 1, t))
        return transactions
    
    def receive_transaction(self, transaction):
        self.transactions.add(transaction)

    def forward_transaction(self, transaction):
        # The structure of self.routing_table is:
        # {recipient_peer: [list of TxIDs either sent to or received from this peer]}

        for n in self.neighbors:
            id = transaction.id
            if n in self.routing_table.keys():
                # Send this transaction to that neighbor some how
                n.receive_transaction(transaction)
                if id not in self.routing_table[n]:
                    self.routing_table[n].append(id)            
            else:
                # Send this transaction to that neighbor some how
                n.receive_transaction(transaction)
                self.routing_table[n] = [id]


    def receive_block(self, block):
        if block.height > self.longest_chain.height:
            self.longest_chain = block
            self.balance = block.balances[self.id]
        elif block.height == self.longest_chain.height and block.timestamp < self.longest_chain.timestamp:
            self.longest_chain = block
            self.balance = block.balances[self.id]

    def create_block(self):
        longest_chain_transactions = self.longest_chain.get_all_transactions()
        valid_transactions = self.transactions - longest_chain_transactions

        num_transactions = random.randint(0, min(len(valid_transactions), 999))

        transactions = random.sample(valid_transactions, num_transactions)

        block = Block(self.longest_chain.height + 1, self.longest_chain, time.time(), transactions, self.id)

        # Next block timestamp (tk + Tk)
        Tk = random.expovariate(self.hashing_power/I)

        # Check if the longest is still persistent at tk + Tk
        # Else don't broadcast
        sim.broadcast(self, block, time.time() + Tk)

    def receive_block(self, block):
        # validate the block
        pass