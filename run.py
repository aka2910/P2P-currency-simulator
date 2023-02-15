import argparse
import simpy
from peer import Peer
from block import Block
from network import Network
import random

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P2P currency simulator")
    parser.add_argument("--n", type=int, default=10, help="Number of peers")
    parser.add_argument("--z0", type=float, default=0.5, help = "percent of slow peers")
    parser.add_argument("--z1", type=float, default=0.5, help = "percent of low CPU peers")
    parser.add_argument("--Ttx", type=float, default=0.5, help = "mean interarrival time of transactions")
    parser.add_argument("--time", type=float, default=100, help = "simulation time")
    parser.add_argument("--I", type=float, default=0.5, help = "mean interarrival time of blocks")

    args = parser.parse_args()

    env = simpy.Environment()
    genesis = Block(None, 0, set([]), -1)

    num_slow = int(args.n*args.z0/100)
    slow_peers = random.sample(range(args.n+1), num_slow)
    
    num_low = int(args.n*args.z1/100)
    low_peers = random.sample(range(args.n+1), num_low)

    # Generate the peers
    peers = []
    for i in range(args.n):
        config = {}
        if i in slow_peers:
            config["speed"] = "slow"
        else:
            config["speed"] = "fast"

        if i in low_peers:
            config["cpu"] = "low"
            config["hashing power"] = 1/(10*args.n - 9*num_low)
        else:
            config["cpu"] = "high"
            config["hashing power"] = 10/(10*args.n - 9*num_low)

        p = Peer(i, genesis, env, config)
        peers.append(p)
        genesis.balances = {i: 0 for i in range(args.n)}

    # Generate the network
    network = Network(peers, args.I, env)

    for peer in peers:
        peer.use_network(network)
        env.process(peer.generate_transactions(args.Ttx, peers))
        env.process(peer.create_block())

    env.run(until=args.time)

    for peer in peers:
        peer.print_tree(f"plots/tree_{peer.id}.dot")