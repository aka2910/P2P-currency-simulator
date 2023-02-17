# P2P-currency-simulator

Requirements:
- Python
- Graphviz
- SimPy

To run the simulation, run the following command:

```python
python3 run.py --n 50 --z0 0.8 --z1 0.3 --Ttx 1 --I 1 --time 1000
```

The parameters are:
- n: number of peers
- z0: percent of slow peers
- z1: percent of low CPU peers
- Ttx: mean interarrival time of transactions
- I: mean interarrival time of blocks
- time: simulation time

The graph for each peer (block tree) is generated in the folder "plots_{n}".
