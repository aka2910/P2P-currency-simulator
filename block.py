class Block:
    def __init__(self, prevblock, timestamp, transactions, userid):
        self.prevblock = prevblock
        self.timestamp = timestamp
        self.transactions = transactions
        self.userid = userid

        trans_string = ""
        for transaction in transactions:
            trans_string += str(transaction) + " "
        
        if prevblock == None:
            self.balances = {}
            self.height = 0
            self.blkid = hash(str(timestamp))
        else:
            self.balances = self.prevblock.balances.copy()
            self.height = self.prevblock.height + 1
            self.blkid = hash(str(prevblock.blkid) + str(timestamp) + str(trans_string) + str(userid))

        # Size in Kb
        self.size = 8*(len(transactions) + 1)

    def validate(self):
        # check if the transactions are valid
        balance_copy = self.balances.copy()
        for t in self.transactions:
            # if t.sender == t.receiver:
            #     return False
            if t.amount <= 0:
                return False
            if balance_copy[t.sender.id] < t.amount:
                # Changing self.balances to balance_copy because I think
                # that the current balance should be enough to pay for
                return False
            balance_copy[t.sender.id] -= t.amount
            balance_copy[t.receiver.id] += t.amount
        self.balances = balance_copy

        self.balances[self.userid] += 50
        return True

    def get_all_transactions(self):
        if self.prevblock == None:
            return self.transactions
        return self.transactions.union(self.prevblock.get_all_transactions())
    
    def __str__(self):
        return self.blkid