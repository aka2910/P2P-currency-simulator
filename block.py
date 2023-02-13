class Block:
    def __init__(self, blkid, prevblkid, timestamp, transactions):
        self.blkid = blkid
        self.prevblkid = prevblkid
        self.timestamp = timestamp
        self.transactions = transactions

    def valid_transactions(self):
        # check if the transactions are valid
        for t in self.transactions:
            if t.sender == t.receiver:
                return False
            if t.amount <= 0:
                return False
            if t.sender.balance < t.amount:
                return False
        return True
        
        