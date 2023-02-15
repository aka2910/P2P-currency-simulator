import argparse
import simpy

class Simulator():
    def __init__(self) -> None:
        pass

    def broadcast(self, peer, msg, time):
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P2P currency simulator")
    parser.add_argument("--n", type=int, default=10, help="Number of peers")
    parser.add_argument("--z0", type=float, default=0.5, help = "percent of slow peers")
    parser.add_argument("--z1", type=float, default=0.5, help = "percent of low CPU peers")
    parser.add_argument("--Ttx", type=float, default=0.5, help = "mean interarrival time of transactions")
    parser.add_argument("--time", type=float, default=100, help = "simulation time")

    env = simpy.Environment()
    # env.process()
    # env.run(until=100)