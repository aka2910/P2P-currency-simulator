import random 
from transaction import Transaction

class Peer:
    def __init__(self, id) -> None:
        self.id = id
        self.neighbors = []
        self.speed = "" # slow or fast 
        self.cpu = ""   # low or high

    
    def add_neighbor(self, neighbor):
        self.neighbors.append(neighbor)

    def disconnect_peer(self):
        self.neighbors = []
    
    def generate_transactios(self, Ttx, time, peers):
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
    

class Network:
    def __init__(self, peers) -> None:
        self.peers = peers
        self.transactions = []

    def generate_network(self):
        for peer in self.peers:
            num_neighbors = random.randint(4, 8)
            num_neighbors = min(num_neighbors, len(self.peers))

            temp_list = self.peers.copy() - [peer]
            neighbors = random.sample(temp_list, num_neighbors)

            for n in neighbors:
                peer.add_neighbor(n)
                n.add_neighbor(peer)

    def check_graph(self):
        # check if the graph is connected
        # if not, connect the graph
        
        visited = [False for i in range(len(self.peers))]

        def dfs(node):
            visited[node.id] = True
            for n in node.neighbors:
                if not visited[n.id]:
                    dfs(n)
        dfs(self.peers[0])
        connected = True

        for i in range(len(visited)):
            if not visited[i]:
                connected = False

        if not connected:
            # connect the graph
            num_peers = len(self.peers)
            for i in range(num_peers):
                peer = self.peers[i]
                peer.disconnect_peer()

                for j in range(4):
                    peer.add_neighbor(self.peers[(i+j-2)%num_peers])
                    peer.add_neighbor(self.peers[(i+j-1)%num_peers])
                    peer.add_neighbor(self.peers[(i+j+1)%num_peers])
                    peer.add_neighbor(self.peers[(i+j+2)%num_peers])
                    