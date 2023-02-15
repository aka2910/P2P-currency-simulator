import random 

class Network:
    def __init__(self, peers, interarrival, env) -> None:
        self.peers = peers
        self.peer_ids = []
        self.interarrival = interarrival

        for i in range(len(self.peers)):
            self.peer_ids.append(self.peers[i].id)

        self.generate_network()
        self.check_graph()
        self.init_properties()

        self.env = env

    def generate_network(self):
        for peer in self.peers:
            num_neighbors = random.randint(4, 8)
            num_neighbors = min(num_neighbors, len(self.peers))

            temp_list = list(set(self.peers.copy()) - set([peer]))
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
                    

    def init_properties(self):
        self.p = [[0 for i in range(len(self.peers))] for j in range(len(self.peers))]
        self.c = [[0 for i in range(len(self.peers))] for j in range(len(self.peers))]
        self.d = [[None for i in range(len(self.peers))] for j in range(len(self.peers))]

        for i in range(len(self.peers)):
            for j in range(len(self.peers)):
                if i == j:
                    self.p[i][j] = 0
                    self.c[i][j] = 0
                    self.d[i][j] = None
                else:
                    # Init the propagation delay
                    val = self.p[j][i]
                    
                    # In ms
                    if val != 0:
                        self.p[i][j] = val
                    else:
                        r = random.randint(10, 500)
                        self.p[i][j] = r

                    # Init the computation delay
                    speed_i = self.peers[i].speed
                    speed_j = self.peers[j].speed

                    # In Mbps
                    if speed_i == 'fast' and speed_j == 'fast':
                        self.c[i][j] = 100
                    else:
                        self.c[i][j] = 5

                    # Init the queueing delay
                    # In ms
                    if self.d[j][i] is not None:
                        self.d[i][j] = self.d[j][i]
                    else:
                        # def f(c, i, j):
                        #     print("c:", c)
                        #     print("i:", i, "j:", j)         
                        #     print("exp", random.expovariate(c/96))
                        #     return random.expovariate(c/96)   
                        self.d[i][j] = random.expovariate

    def send_transaction(self, sender, receiver, transaction):
        # print("Send transaction from", sender.id, "to", receiver.id)
        latency = self.p[sender.id][receiver.id] + 8/self.c[sender.id][receiver.id] + self.d[sender.id][receiver.id](self.c[sender.id][receiver.id]/96)
        # print("Latency:", latency)

        yield self.env.timeout(latency)
        yield self.env.process(receiver.receive_transaction(transaction))

    def send_block(self, sender, receiver, block):
        latency = self.p[sender.id][receiver.id] + block.size/self.c[sender.id][receiver.id] + self.d[sender.id][receiver.id](self.c[sender.id][receiver.id]/96)
        yield self.env.timeout(latency)
        yield self.env.process(receiver.receive_block(block))